#
# Thierry Parmentelat - INRIA
# 

import re
from types import StringTypes

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Table import Row, Table

from PLC.ForeignNodes import ForeignNodes,ForeignNode

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
	'node_ids' : Parameter ([int], "This peer's nodes ids")
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

    def manage_node (self, foreign_node, foreign_id, commit=True):
        """
        associate/dissociate a foreign node to/from a peer
        foreign_node is a local object that describes a remote node
        foreign_id is the unique id as provided by the remote peer
        convention is:
           if foreign_id is None : performs dissociation
           otherwise:              performs association
        """

        assert 'peer_id' in self
        assert 'node_id' in foreign_node

        peer_id = self['peer_id']
        node_id = foreign_node ['node_id']

        if foreign_id:
            ### ADDING
            sql = "INSERT INTO peer_node VALUES (%d,%d,%d)" % (peer_id,node_id,foreign_id)
            self.api.db.do(sql)
            if self['node_ids'] is None:
                self['node_ids']=[node_id,]
            self['node_ids'].append(node_id)
            ### DELETING
        else:
            sql = "DELETE FROM peer_node WHERE peer_id=%d AND node_id=%d" % (peer_id,node_id)
            self.api.db.do(sql)
            self['node_ids'].remove(node_id)

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
        # new to index it by hostname for searching later
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
            foreign_id = node ['node_id']
            try:
                foreign_node = local_foreign_nodes_index[hostname]
                if foreign_node['peer_id'] != peer_id:
                    ### the node has changed its plc, needs to update peer_node
                    old_peer_id = foreign_node['peer_id']
                    old_peers=Peers(self.api,[peer_id])
                    assert old_peer[0]
                    # remove from previous peer
                    old_peers[0].manage_node(foreign_node,None,False)
                    # add to new peer
                    self.manage_node(foreign_node,foreign_id,True)
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
                self.manage_node(new_foreign_node,foreign_id,True)
                local_foreign_nodes_index[hostname]=new_foreign_node

	### delete entries that are not uptodate
        for foreign_node in local_foreign_nodes:
            if not foreign_node.uptodate:
                foreign_node.delete()

        return len(peer_get_nodes)-old_count
        
    def refresh_slices (self, peer_get_slices):
        return 0

        
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
