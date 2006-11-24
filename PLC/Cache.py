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
    
    # the Peer object we are syncing with
    def __init__ (self, api, peer, peer_server, auth):

	import PLC.Peers

	self.api = api
        assert isinstance(peer,PLC.Peers.Peer)
        self.peer = peer
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
	    verbose ('entering transcode with alien_id',alien_id,)
	    alien_object=self.alien_objects_byid[alien_id]
	    verbose ('located alien_obj',)
	    name = alien_object [self.class_key]
	    verbose ('got name',name,)
	    local_object=self.local_objects_byname[name]
	    verbose ('found local obj')
	    local_id=local_object[self.primary_key]
	    verbose ('and local_id',local_id)
	    return local_id
	    

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
        ### xxx needs to be optimized
        ### tried to figure a way to use a single sql statement
        ### like: insert into table (x,y) values (1,2),(3,4);
        ### but apparently this is not supported under postgresql
	    for id2 in id2_set:
		sql = "INSERT INTO %s VALUES (%d,%d)"%(self.tablename,id1,id2)
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
    # his must match the keys in xref_specs
    # lambda_ignore : the alien objects are ignored if this returns true
    def update_table (self,
                      classname,
                      alien_object_list,
		      alien_xref_objs_dict = {},
                      lambda_ignore=lambda x:False):
        
        peer = self.peer
        peer_id = peer['peer_id']

	attrs = class_attributes (classname)
	row_class = attrs['row_class']
	table_class = attrs['table_class']
	primary_key = attrs['primary_key']
	class_key = attrs['class_key']
	foreign_fields = attrs['foreign_fields']
	foreign_xrefs = attrs['foreign_xrefs']

	## allocate transcoders and xreftables once, for each item in foreign_xrefs
	# create a dict 'classname' -> {'transcoder' : ..., 'xref_table' : ...}
	accessories = dict(
	    [ (xref_classname,
	       {'transcoder':Cache.Transcoder (self.api,xref_classname,alien_xref_objs_dict[xref_classname]),
		'xref_table':Cache.XrefTable (self.api,xref_spec['table'],classname,xref_classname)})
	      for xref_classname,xref_spec in foreign_xrefs.iteritems()])

        ### get current local table
        # get ALL local objects so as to cope with
	# (*) potential moves between plcs
	# (*) or naming conflicts
        local_objects = table_class (self.api)
        ### index upon class_key for future searches
	#verbose ('local objects:',local_objects)
	verbose ('class_key',class_key)
        local_objects_index = local_objects.dict(class_key)
	verbose ('update_table',classname,local_objects_index.keys())

	### mark entries for this peer outofdate
        old_count=0;
	for local_object in local_objects:
	    if local_object['peer_id'] == peer_id:
		local_object.uptodate=False
                old_count += 1
	    else:
		local_object.uptodate=True

        new_count=0
        # scan the peer's local objects
        for alien_object in alien_object_list:

            object_name = alien_object[class_key]

            ### ignore, e.g. system-wide slices
            if lambda_ignore(alien_object):
		verbose('Ignoring',object_name)
                continue

	    verbose ('update_table - Considering',object_name)
                
            # create or update
            try:
                ### We know about this object already
                local_object = local_objects_index[object_name]
		if local_object ['peer_id'] is None:
		    ### xxx send e-mail
		    print '==================== We are in trouble here'
		    print 'The %s object named %s is natively defined twice'%(classname,object_name)
		    print 'Once on this PLC and once on peer %d'%peer_id
		    print 'We dont raise an exception so that the remaining updates can still take place'
		    continue
                if local_object['peer_id'] != peer_id:
                    ### the object has changed its plc, 
		    ### Note, this is not problematic here because both definitions are remote
		    ### we can assume the object just moved
		    ### needs to update peer_id though
                    local_object['peer_id'] = peer_id
		verbose ('update_table FOUND',object_name)
	    except:
                ### create a new entry
                local_object = row_class(self.api,
					  {class_key :object_name,'peer_id':peer_id})
                # insert in index
                local_objects_index[class_key]=local_object
		verbose ('update_table CREATED',object_name)

            # go on with update
            for field in foreign_fields:
                local_object[field]=alien_object[field]

            # this row is now valid
            local_object.uptodate=True
            new_count += 1
            local_object.sync()

	    # manage cross-refs
	    for xref_classname,xref_spec in foreign_xrefs.iteritems():
		field=xref_spec['field']
		alien_xref_obj_list = alien_xref_objs_dict[xref_classname]
		alien_value = alien_object[field]
		if isinstance (alien_value,list):
		    verbose ('update_table list-transcoding ',xref_classname,' aliens=',alien_value,)
		    transcoder = accessories[xref_classname]['transcoder']
		    local_values=[]
		    for a in alien_value:
			try:
			    local_values.append(transcoder.transcode(a))
			except:
			    # could not transcode - might be from another peer that we dont know about..
			    pass
		    verbose (" transcoded as ",local_values)
		    xref_table = accessories[xref_classname]['xref_table']
		    # newly created objects dont have xrefs yet
		    try:
			former_xrefs=local_object[xref_spec['field']]
		    except:
			former_xrefs=[]
		    xref_table.update_item (local_object[primary_key],
					    former_xrefs,
					    local_values)
		elif isinstance (alien_value,int):
		    new_value = transcoder.transcode(alien_value)
		    local_object[field] = new_value
		    local_object.sync()

	### delete entries that are not uptodate
        for local_object in local_objects:
            if not local_object.uptodate:
                local_object.delete()

        self.api.db.commit()

        ### return delta in number of objects 
        return new_count-old_count
                
    def get_locals (self, list):
	return [x for x in list if x['peer_id'] is None]

    def refresh_peer (self):
	
	# so as to minimize the numer of requests
	# we get all objects in a single call and sort afterwards
	# xxx ideally get objects either local or the ones attached here
	# requires to know remote peer's peer_id for ourselves, mmhh..
	# does not make any difference in a 2-peer deployment though

	# refresh keys
	all_keys = self.peer_server.GetKeys(self.auth)
	local_keys = self.get_locals (all_keys)
	nb_new_keys = self.update_table('Key', local_keys)

	# refresh nodes
        all_nodes = self.peer_server.GetNodes(self.auth)
	local_nodes = self.get_locals(all_nodes)
        nb_new_nodes = self.update_table('Node', local_nodes)

	# refresh persons
	all_persons = self.peer_server.GetPersons(self.auth)
	local_persons = self.get_locals(all_persons)
	nb_new_persons = self.update_table ('Person', local_persons,
					    { 'Key': all_keys} )

	# refresh slices
        local_slices = self.peer_server.GetSlices(self.auth,{'peer_id':None})

	def is_system_slice (slice):
	    return slice['creator_person_id'] == 1

        nb_new_slices = self.update_table ('Slice', local_slices,
					   {'Node': all_nodes,
					    'Person': all_persons},
					   is_system_slice)

        return {'plcname':self.api.config.PLC_NAME,
		'new_keys':nb_new_keys,
                'new_nodes':nb_new_nodes,
		'new_persons':nb_new_persons,
                'new_slices':nb_new_slices}

