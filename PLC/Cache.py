import time

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Table import Row, Table

verbose_flag=False;
#verbose_flag=True;
def verbose (*args):
    if verbose_flag:
	print (args)

def class_attributes (classname):
    """ locates various attributes defined in the row class """
    topmodule = __import__ ('PLC.%ss'%classname)
    module = topmodule.__dict__['%ss'%classname]
    # local row-like class, e.g. Node
    row_class = module.__dict__['%s'%classname]
    # local tab-like class, e.g. Nodes
    table_class = module.__dict__['%ss'%classname]

    return {'row_class':row_class, 
	    'table_class':table_class,
	    'primary_key': row_class.__dict__['primary_key'],
	    'class_key': row_class.__dict__['class_key'],
	    'foreign_fields': row_class.__dict__['foreign_fields'],
	    'foreign_xrefs': row_class.__dict__['foreign_xrefs'],
	    }

class Cache:

    # an attempt to provide genericity in the caching algorithm
    
    def __init__ (self, api, peer_id, peer_server, auth):

	self.api = api
        self.peer_id = peer_id
	self.peer_server = peer_server
	self.auth = auth
        
    class Transcoder:

	def __init__ (self, api, classname, alien_objects):
	    self.api = api
	    attrs = class_attributes (classname)
	    self.primary_key = attrs['primary_key']
	    self.class_key = attrs['class_key']

	    # cannot use dict, it's acquired by xmlrpc and is untyped
	    self.alien_objects_byid = dict( [ (x[self.primary_key],x) for x in alien_objects ] )

	    # retrieve local objects
	    local_objects = attrs['table_class'] (api)
	    self.local_objects_byname = local_objects.dict(self.class_key)

	    verbose ('Transcoder init :',classname,
		     self.alien_objects_byid.keys(),
		     self.local_objects_byname.keys())

	def transcode (self, alien_id):
	    """ transforms an alien id into a local one """
	    # locate alien obj from alien_id
	    #verbose ('.entering transcode with alien_id',alien_id,)
	    alien_object=self.alien_objects_byid[alien_id]
	    #verbose ('..located alien_obj',)
	    name = alien_object [self.class_key]
	    #verbose ('...got name',name,)
	    local_object=self.local_objects_byname[name]
	    #verbose ('....found local obj')
	    local_id=local_object[self.primary_key]
	    #verbose ('.....and local_id',local_id)
	    return local_id
	    

    # for handling simple n-to-n relation tables, like e.g. slice_node
    class XrefTable: 

	def __init__ (self, api, tablename, class1, class2):
	    self.api = api
	    self.tablename = tablename
	    self.lowerclass1 = class1.lower()
	    self.lowerclass2 = class2.lower()

	def delete_old_items (self, id1, id2_set):
	    if id2_set:
		sql = ""
		sql += "DELETE FROM %s WHERE %s_id=%d"%(self.tablename,self.lowerclass1,id1)
		sql += " AND %s_id IN ("%self.lowerclass2
		sql += ",".join([str(i) for i in id2_set])
		sql += ")"
		self.api.db.do (sql)

	def insert_new_items (self, id1, id2_set):
	    if id2_set:
		sql = "INSERT INTO %s select %d, %d " % \
   			self.tablename, id1, id2[0] 
	    	for id2 in id2_set[1:]:
			sql += " UNION ALL SELECT %d, %d " % \
			(id1,id2)
		self.api.db.do (sql)

	def update_item (self, id1, old_id2s, new_id2s):
	    news = set (new_id2s)
	    olds = set (old_id2s)
	    to_delete = olds-news
	    self.delete_old_items (id1, to_delete)
	    to_create = news-olds
	    self.insert_new_items (id1, to_create)
	    self.api.db.commit()
	    
    # classname: the type of objects we are talking about;       e.g. 'Slice'
    # peer_object_list list of objects at a given peer -         e.g. peer.GetSlices()
    # alien_xref_objs_dict : a dict {'classname':alien_obj_list} e.g. {'Node':peer.GetNodes()}
    #    we need an entry for each class mentioned in the class's foreign_xrefs
    # lambda_ignore : the alien objects are ignored if this returns true
    def update_table (self,
                      classname,
                      alien_object_list,
		      alien_xref_objs_dict = {},
                      lambda_ignore=lambda x:False,
                      report_name_conflicts = True):
        
        verbose ("============================== entering update_table on",classname)
        peer_id=self.peer_id

	attrs = class_attributes (classname)
	row_class = attrs['row_class']
	table_class = attrs['table_class']
	primary_key = attrs['primary_key']
	class_key = attrs['class_key']
	foreign_fields = attrs['foreign_fields']
	foreign_xrefs = attrs['foreign_xrefs']

	## allocate transcoders and xreftables once, for each item in foreign_xrefs
	# create a dict 'classname' -> {'transcoder' : ..., 'xref_table' : ...}
        xref_accessories = dict(
            [ (xref['field'],
               {'transcoder' : Cache.Transcoder (self.api,xref['class'],alien_xref_objs_dict[xref['class']]),
                'xref_table' : Cache.XrefTable (self.api,xref['table'],classname,xref['class'])})
              for xref in foreign_xrefs ])

        # the fields that are direct references, like e.g. site_id in Node
        # determined lazily, we need an alien_object to do that, and we may have none here
        direct_ref_fields = None

        ### get current local table
        # get ALL local objects so as to cope with
	# (*) potential moves between plcs
	# (*) or naming conflicts
        local_objects = table_class (self.api)
        ### index upon class_key for future searches
        local_objects_index = local_objects.dict(class_key)

	#verbose ('update_table',classname,local_objects_index.keys())

	### mark entries for this peer outofdate
        new_count=0
        old_count=0;
	for local_object in local_objects:
	    if local_object['peer_id'] == peer_id:
		local_object.uptodate=False
                old_count += 1
	    else:
		local_object.uptodate=True

        # scan the peer's local objects
        for alien_object in alien_object_list:

            object_name = alien_object[class_key]

            ### ignore, e.g. system-wide slices
            if lambda_ignore(alien_object):
		verbose('Ignoring',object_name)
                continue

	    verbose ('update_table (%s) - Considering'%classname,object_name)
                
            # create or update
            try:
                ### We know about this object already
                local_object = local_objects_index[object_name]
		if local_object ['peer_id'] is None:
                    if report_name_conflicts:
		        ### xxx send e-mail
                        print '!!!!!!!!!! We are in trouble here'
                        print 'The %s object named %s is natively defined twice, '%(classname,object_name),
                        print 'once on this PLC and once on peer %d'%peer_id
                        print 'We dont raise an exception so that the remaining updates can still take place'
                        print '!!!!!!!!!!'
		    continue
                if local_object['peer_id'] != peer_id:
                    ### the object has changed its plc, 
		    ### Note, this is not problematic here because both definitions are remote
		    ### we can assume the object just moved
		    ### needs to update peer_id though
                    local_object['peer_id'] = peer_id
                # update all fields as per foreign_fields
                for field in foreign_fields:
                    local_object[field]=alien_object[field]
		verbose ('update_table FOUND',object_name)
	    except:
                ### create a new entry
                local_object = row_class(self.api,
					  {class_key :object_name,'peer_id':peer_id})
                # insert in index
                local_objects_index[class_key]=local_object
		verbose ('update_table CREATED',object_name)
                # update all fields as per foreign_fields
                for field in foreign_fields:
                    local_object[field]=alien_object[field]
                # this is tricky; at this point we may have primary_key unspecified,
                # but we need it for handling xrefs below, so we'd like to sync to get one
                # on the other hand some required fields may be still missing so
                #  the DB would refuse to sync in this case (e.g. site_id in Node)
                # so let's fill them with 1 so we can sync, this will be overridden below
                # lazily determine this set of fields now
                if direct_ref_fields is None:
                    direct_ref_fields=[]
                    for xref in foreign_xrefs:
                        field=xref['field']
                        verbose('checking field %s for direct_ref'%field)
                        if isinstance(alien_object[field],int):
                            direct_ref_fields.append(field)
                    verbose("FOUND DIRECT REFS",direct_ref_fields)
                for field in direct_ref_fields:
                    local_object[field]=1
                verbose('Early sync on',local_object)
                local_object.sync()

            # this row is now valid
            local_object.uptodate=True
            new_count += 1

	    # manage cross-refs
	    for xref in foreign_xrefs:
		field=xref['field']
		alien_xref_obj_list = alien_xref_objs_dict[xref['class']]
		alien_value = alien_object[field]
		transcoder = xref_accessories[xref['field']]['transcoder']
		if isinstance (alien_value,list):
		    #verbose ('update_table list-transcoding ',xref['class'],' aliens=',alien_value,)
		    local_values=[]
		    for a in alien_value:
			try:
			    local_values.append(transcoder.transcode(a))
			except:
			    # could not transcode - might be from another peer that we dont know about..
			    pass
		    #verbose (" transcoded as ",local_values)
		    xref_table = xref_accessories[xref['field']]['xref_table']
		    # newly created objects dont have xref fields set yet
		    try:
			former_xrefs=local_object[xref['field']]
		    except:
			former_xrefs=[]
		    xref_table.update_item (local_object[primary_key],
					    former_xrefs,
					    local_values)
		elif isinstance (alien_value,int):
		    #verbose ('update_table atom-transcoding ',xref['class'],' aliens=',alien_value,)
		    new_value = transcoder.transcode(alien_value)
		    local_object[field] = new_value

            ### this object is completely updated, let's save it
            verbose('FINAL sync on %s:'%object_name,local_object)
            local_object.sync()
                    

	### delete entries that are not uptodate
        for local_object in local_objects:
            if not local_object.uptodate:
                local_object.delete()

        self.api.db.commit()

        ### return delta in number of objects 
        return new_count-old_count

    # slice attributes exhibit a special behaviour
    # because there is no name we can use to retrieve/check for equality
    # this object is like a 3-part xref, linking slice_attribute_type, slice,
    #    and potentially node, together with a value that can change over time.
    # extending the generic model to support a lambda rather than class_key
    #    would clearly become overkill
    def update_slice_attributes (self,
                                 alien_slice_attributes,
                                 alien_nodes,
                                 alien_slices):

        from PLC.SliceAttributeTypes import SliceAttributeTypes
        from PLC.SliceAttributes import SliceAttribute, SliceAttributes

        # init
        peer_id = self.peer_id
        
        # create transcoders
        node_xcoder = Cache.Transcoder (self.api, 'Node', alien_nodes)
        slice_xcoder= Cache.Transcoder (self.api, 'Slice', alien_slices)
        # no need to transcode SliceAttributeTypes, we have a name in the result
        local_sat_dict = SliceAttributeTypes(self.api).dict('name')
               
        # load local objects
        local_objects = SliceAttributes (self.api,{'peer_id':peer_id})

	### mark entries for this peer outofdate
        new_count = 0
        old_count=len(local_objects)
	for local_object in local_objects:
            local_object.uptodate=False

        for alien_object in alien_slice_attributes:

            verbose('----- update_slice_attributes: considering ...')
            verbose('   ',alien_object)

            # locate local slice
            try:
                slice_id = slice_xcoder.transcode(alien_object['slice_id'])
            except:
                verbose('update_slice_attributes: unable to locate slice',
                        alien_object['slice_id'])
                continue
            # locate slice_attribute_type
            try:
                sat_id = local_sat_dict[alien_object['name']]['attribute_type_id']
            except:
                verbose('update_slice_attributes: unable to locate slice attribute type',
                        alien_object['name'])
                continue
            # locate local node if specified
            try:
                alien_node_id = alien_object['node_id']
                if alien_node_id is not None:
                    node_id = node_xcoder.transcode(alien_node_id)
                else:
                    node_id=None
            except:
                verbose('update_slice_attributes: unable to locate node',
                        alien_object['node_id'])
                continue

            # locate the local SliceAttribute if any
            try:
                verbose ('searching name=', alien_object['name'],
                         'slice_id',slice_id, 'node_id',node_id)
                local_object = SliceAttributes (self.api,
                                                {'name':alien_object['name'],
                                                 'slice_id':slice_id,
                                                 'node_id':node_id})[0]
                
                if local_object['peer_id'] != peer_id:
                    verbose ('FOUND local sa - skipped')
                    continue
                verbose('FOUND already cached sa - setting value')
                local_object['value'] = alien_object['value']
            # create it if missing
            except:
                local_object = SliceAttribute(self.api,
                                              {'peer_id':peer_id,
                                               'slice_id':slice_id,
                                               'node_id':node_id,
                                               'attribute_type_id':sat_id,
                                               'value':alien_object['value']})
                verbose('CREATED new sa')
            local_object.uptodate=True
            new_count += 1
            local_object.sync()

        for local_object in local_objects:
            if not local_object.uptodate:
                local_object.delete()

        self.api.db.commit()
        ### return delta in number of objects 
        return new_count-old_count

    def refresh_peer (self):
	
	# so as to minimize the numer of requests
	# we get all objects in a single call and sort afterwards
	# xxx ideally get objects either local or the ones attached here
	# requires to know remote peer's peer_id for ourselves, mmhh..
	# does not make any difference in a 2-peer deployment though

        ### uses GetPeerData to gather all info in a single xmlrpc request

        t_start=time.time()
        # xxx see also GetPeerData - peer_id arg unused yet
        all_data = self.peer_server.GetPeerData (self.auth,0)

        t_acquired = time.time()
	# refresh sites
	plocal_sites = all_data['Sites-local']
        all_sites = plocal_sites + all_data['Sites-peer']
	nb_new_sites = self.update_table('Site', plocal_sites)

	# refresh keys
	plocal_keys = all_data['Keys-local']
        all_keys = plocal_keys + all_data['Keys-peer']
	nb_new_keys = self.update_table('Key', plocal_keys)

	# refresh nodes
	plocal_nodes = all_data['Nodes-local']
        all_nodes = plocal_nodes + all_data['Nodes-peer']
        nb_new_nodes = self.update_table('Node', plocal_nodes,
					 { 'Site' : all_sites } )

	# refresh persons
	plocal_persons = all_data['Persons-local']
        all_persons = plocal_persons + all_data['Persons-peer']
	nb_new_persons = self.update_table ('Person', plocal_persons,
					    { 'Key': all_keys, 'Site' : all_sites } )

        # refresh slice attribute types
        plocal_slice_attribute_types = all_data ['SliceAttibuteTypes-local']
        nb_new_slice_attribute_types = self.update_table ('SliceAttributeType',
                                                          plocal_slice_attribute_types,
                                                          report_name_conflicts = False)

	# refresh slices
        plocal_slices = all_data['Slices-local']
        all_slices = plocal_slices + all_data['Slices-peer']

	def is_system_slice (slice):
	    return slice['creator_person_id'] == 1

        nb_new_slices = self.update_table ('Slice', plocal_slices,
                                           {'Node': all_nodes,
                                            'Person': all_persons,
                                            'Site': all_sites},
					   is_system_slice)

        # refresh slice attributes
        plocal_slice_attributes = all_data ['SliceAttributes-local']
        nb_new_slice_attributes = self.update_slice_attributes (plocal_slice_attributes,
                                                                all_nodes,
                                                                all_slices)
        
        t_end=time.time()
        ### returned as-is by RefreshPeer
        return {'plcname':self.api.config.PLC_NAME,
		'new_sites':nb_new_sites,
		'new_keys':nb_new_keys,
                'new_nodes':nb_new_nodes,
		'new_persons':nb_new_persons,
                'new_slice_attribute_types':nb_new_slice_attribute_types,
                'new_slices':nb_new_slices,
                'new_slice_attributes':nb_new_slice_attributes,
                'time_gather': all_data['ellapsed'],
                'time_transmit':t_acquired-t_start-all_data['ellapsed'],
                'time_process':t_end-t_acquired,
                'time_all':t_end-t_start,
                }

