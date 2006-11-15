#
# Thierry Parmentelat - INRIA
# 

import re
from types import StringTypes

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Table import Row, Table

from PLC.Nodes import Nodes,Node
from PLC.ForeignNodes import ForeignNodes,ForeignNode
from PLC.ForeignSlices import ForeignSlices,ForeignSlice

class Peer (Row):
    """
    Stores the list of peering PLCs in the peers table. 
    See the Row class for more details
    """

    table_name = 'peers'
    primary_key = 'peer_id'
    fields = {
	'peer_id' : Parameter (int, "Peer identifier"),
	'peername' : Parameter (str, "Peer name"),
	'peer_url' : Parameter (str, "Peer API url"),
	'person_id' : Parameter (int, "Person_id of the account storing credentials - temporary"),
	'node_ids' : Parameter ([int], "This peer's nodes ids"),
	'slice_ids' : Parameter ([int], "This peer's slices ids"),
	}

    def validate_peer_url (self, url):
	"""
	Validate URL, checks it looks like https 
	"""
	invalid_url = PLCInvalidArgument("Invalid URL")
	if not re.compile ("^https://.*$").match(url) : 
	    raise invalid_url
	return url

    def delete (self, commit=True):
	"""
	Delete peer
	"""
	
	assert 'peer_id' in self

        # remove nodes depending on this peer
        for foreign_node_id in self.get_foreign_nodes():
            try:
                foreign_node = ForeignNodes(self.api,[foreign_node_id])[0]
                foreign_node.delete(commit)
            except:
                print "Glitch : a foreign node instance was uncleanly deleted"

        # remove the peer
	self['deleted'] = True
	self.sync(commit)

    def get_foreign_nodes (self):
        """
        returns a list of the foreign nodes in this peer
        """
        sql="SELECT node_ids FROM peer_nodes WHERE peer_id=%d"%self['peer_id']
        node_ids = self.api.db.selectall(sql)
        return node_ids[0]['node_ids']

    def manage_node (self, foreign_node, add_if_true, commit=True):
        """
        associate/dissociate a foreign node to/from a peer
        foreign_node is a local object that describes a remote node
        convention is:
           if add_if_true is None : performs dissociation
           otherwise:               performs association
        """

        assert 'peer_id' in self
        assert 'node_id' in foreign_node

        peer_id = self['peer_id']
        node_id = foreign_node ['node_id']

        if add_if_true:
            ### ADDING
            sql = "INSERT INTO peer_node VALUES (%d,%d)" % (peer_id,node_id)
            self.api.db.do(sql)
            if self['node_ids'] is None:
                self['node_ids']=[node_id,]
            else:
                self['node_ids'].append(node_id)
            ### DELETING
        else:
            sql = "DELETE FROM peer_node WHERE peer_id=%d AND node_id=%d" % (peer_id,node_id)
            self.api.db.do(sql)
            self['node_ids'].remove(node_id)

        if commit:
            self.api.db.commit()

    def manage_slice (self, foreign_slice, add_if_true, commit=True):
        """
        associate/dissociate a foreign node to/from a peer
        foreign_slice is a local object that describes a remote slice
        alien_id is the unique id as provided by the remote peer
        convention is:
           if add_if_true is None : performs dissociation
           otherwise:               performs association
        """

        assert 'peer_id' in self
        assert 'slice_id' in foreign_slice

        peer_id = self['peer_id']
        slice_id = foreign_slice ['slice_id']

        if add_if_true:
            ### ADDING
            sql = "INSERT INTO peer_slice VALUES (%d,%d)" % (peer_id,slice_id)
            self.api.db.do(sql)
            if self['slice_ids'] is None:
                self['slice_ids']=[slice_id,]
            else:
                self['slice_ids'].append(slice_id)
            ### DELETING
        else:
            sql = "DELETE FROM peer_slice WHERE peer_id=%d AND slice_id=%d" % (peer_id,slice_id)
            self.api.db.do(sql)
            self['slice_ids'].remove(slice_id)

        if commit:
            self.api.db.commit()

    def refresh_nodes (self, peer_get_nodes):
        """
        refreshes the foreign_nodes and peer_node tables
        expected input is the current list of nodes as returned by GetNodes

        returns the number of new nodes on this peer (can be negative)
        """

        peer_id = self['peer_id']
        
	# we get the whole table just in case 
	# a host would have switched from one plc to the other
	local_foreign_nodes = ForeignNodes (self.api)
        # index it by hostname for searching later
        local_foreign_nodes_index = local_foreign_nodes.dict('hostname')
	
	### mark entries for this peer outofdate
        old_count=0;
	for foreign_node in local_foreign_nodes:
	    if foreign_node['peer_id'] == peer_id:
		foreign_node.uptodate=False
                old_count += 1

        ### these fields get copied through
        remote_fields = ['boot_state','model','version','date_created','last_updated']

	### scan the new entries, and mark them uptodate
	for node in peer_get_nodes:
	    hostname = node['hostname']
            try:
                foreign_node = local_foreign_nodes_index[hostname]
                if foreign_node['peer_id'] != peer_id:
                    ### the node has changed its plc, needs to update peer_node
                    old_peer_id = foreign_node['peer_id']
                    old_peers=Peers(self.api,[peer_id])
                    assert old_peer[0]
                    # remove from previous peer
                    old_peers[0].manage_node(foreign_node,False,False)
                    # add to new peer
                    self.manage_node(foreign_node,True,True)
                    foreign_node['peer_id'] = peer_id
		### update it anyway: copy other relevant fields
                for field in remote_fields:
                    foreign_node[field]=node[field]
                # this row is now valid
                foreign_node.uptodate=True
                foreign_node.sync()
	    except:
                new_foreign_node = ForeignNode(self.api, {'hostname':hostname})
                for field in remote_fields:
                    new_foreign_node[field]=node[field]
                ### need to sync so we get a node_id
                new_foreign_node.sync()
                new_foreign_node.uptodate = True
                self.manage_node(new_foreign_node,True,True)
                local_foreign_nodes_index[hostname]=new_foreign_node

	### delete entries that are not uptodate
        for foreign_node in local_foreign_nodes:
            if not foreign_node.uptodate:
                foreign_node.delete()

        return len(peer_get_nodes)-old_count
        
    ### transcode node_id
    def locate_alien_node_id_in_foreign_nodes (self, peer_foreign_nodes_dict, alien_id):
        """
        returns a local node_id as transcoded from an alien node_id
        only lookups our local nodes because we dont need to know about other sites
        returns a valid local node_id, or throws an exception
        """
        peer_foreign_node = peer_foreign_nodes_dict[alien_id]
        hostname = peer_foreign_node['hostname']
        return Nodes(self.api,[hostname])[0]['node_id']

    def refresh_slices (self, peer_get_slices, peer_foreign_nodes):
        """
        refreshes the foreign_slices and peer_slice tables
        expected input is the current list of slices as returned by GetSlices

        returns the number of new slices on this peer (can be negative)
        """

        peer_id = self['peer_id']
        
	# we get the whole table just in case 
	# a host would have switched from one plc to the other
	local_foreign_slices = ForeignSlices (self.api)
        # index it by name for searching later
        local_foreign_slices_index = local_foreign_slices.dict('name')
	
	### mark entries for this peer outofdate
        old_count=0;
	for foreign_slice in local_foreign_slices:
	    if foreign_slice['peer_id'] == peer_id:
		foreign_slice.uptodate=False
                old_count += 1

        ### these fields get copied through
        remote_fields = ['instantiation', 'url', 'description',
                         'max_nodes', 'created', 'expires']

	### scan the new entries, and mark them uptodate
        new_count=0
	for slice in peer_get_slices:
            ### ignore system-wide slices
            if slice['creator_person_id'] == 1:
                continue

	    name = slice['name']

            # create or update 
            try:
                foreign_slice = local_foreign_slices_index[name]
                if foreign_slice['peer_id'] != peer_id:
                    ### the slice has changed its plc, needs to update peer_slice
                    old_peer_id = foreign_slice['peer_id']
                    old_peers=Peers(self.api,[peer_id])
                    assert old_peer[0]
                    # remove from previous peer
                    old_peers[0].manage_slice(foreign_slice,False,False)
                    # add to new peer
                    self.manage_slice(foreign_slice,True,True)
                    foreign_slice['peer_id'] = peer_id
	    except:
                foreign_slice = ForeignSlice(self.api, {'name':name})
#                ### xxx temporary 
#                foreign_slice['site_id']=1
                ### need to sync so we get a slice_id
                foreign_slice.sync()
                self.manage_slice(foreign_slice,True,True)
                # insert in index
                local_foreign_slices_index[name]=foreign_slice

            # go on with update
            for field in remote_fields:
                foreign_slice[field]=slice[field]
            # this row is now valid
            foreign_slice.uptodate=True
            new_count += 1
            foreign_slice.sync()

            ### handle node_ids
            # in slice we get a set of node_ids
            # but these ids are RELATIVE TO THE PEER
            # so we need to figure the local node_id for these nodes
            # we do this through peer_foreign_nodes 
            # dictify once
            peer_foreign_nodes_dict = {}
            for foreign_node in peer_foreign_nodes:
                peer_foreign_nodes_dict[foreign_node['node_id']]=foreign_node
            updated_node_ids = []
            for alien_node_id in slice['node_ids']:
                try:
                    local_node_id=self.locate_alien_node_id_in_foreign_nodes(peer_foreign_nodes_dict,alien_node_id)
                    updated_node_ids.append(local_node_id)
                except:
                    # this node_id is not in our scope
                    pass
            foreign_slice.update_slice_nodes (updated_node_ids)

	### delete entries that are not uptodate
        for foreign_slice in local_foreign_slices:
            if not foreign_slice.uptodate:
                foreign_slice.delete()

        return new_count-old_count

class Peers (Table):
    """ 
    Maps to the peers table in the database
    """
    
    def __init__ (self, api, peer_filter = None, columns = None):
        Table.__init__(self, api, Peer, columns)

	sql = "SELECT %s FROM view_peers WHERE deleted IS False" % \
              ", ".join(self.columns)

        if peer_filter is not None:
            if isinstance(peer_filter, (list, tuple, set)):
                # Separate the list into integers and strings
                ints = filter(lambda x: isinstance(x, (int, long)), peer_filter)
                strs = filter(lambda x: isinstance(x, StringTypes), peer_filter)
                peer_filter = Filter(Peer.fields, {'peer_id': ints, 'peername': strs})
                sql += " AND (%s)" % peer_filter.sql(api, "OR")
            elif isinstance(peer_filter, dict):
                peer_filter = Filter(Peer.fields, peer_filter)
                sql += " AND (%s)" % peer_filter.sql(api, "AND")

	self.selectall(sql)
