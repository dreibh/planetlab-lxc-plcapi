#
# Functions for interacting with the nodes table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id$
#

from types import StringTypes
import re

from PLC.Faults import *
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Debug import profile
from PLC.Table import Row, Table
from PLC.Interfaces import Interface, Interfaces
from PLC.BootStates import BootStates

def valid_hostname(hostname):
    # 1. Each part begins and ends with a letter or number.
    # 2. Each part except the last can contain letters, numbers, or hyphens.
    # 3. Each part is between 1 and 64 characters, including the trailing dot.
    # 4. At least two parts.
    # 5. Last part can only contain between 2 and 6 letters.
    good_hostname = r'^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+' \
                    r'[a-z]{2,6}$'
    return hostname and \
           re.match(good_hostname, hostname, re.IGNORECASE)

class Node(Row):
    """
    Representation of a row in the nodes table. To use, optionally
    instantiate with a dict of values. Update as you would a
    dict. Commit to the database with sync().
    """

    table_name = 'nodes'
    primary_key = 'node_id'
    # Thierry -- we use delete on interfaces so the related InterfaceSettings get deleted too
    join_tables = [ 'slice_node', 'peer_node', 'slice_attribute', 
                    'node_session', 'node_slice_whitelist', 
                    'node_tag', 'conf_file_node', 'pcu_node', ]
    fields = {
        'node_id': Parameter(int, "Node identifier"),
        'hostname': Parameter(str, "Fully qualified hostname", max = 255),
        'site_id': Parameter(int, "Site at which this node is located"),
        'boot_state': Parameter(str, "Boot state", max = 20),
        'model': Parameter(str, "Make and model of the actual machine", max = 255, nullok = True),
        'boot_nonce': Parameter(str, "(Admin only) Random value generated by the node at last boot", max = 128),
        'version': Parameter(str, "Apparent Boot CD version", max = 64),
        'ssh_rsa_key': Parameter(str, "Last known SSH host key", max = 1024),
        'date_created': Parameter(int, "Date and time when node entry was created", ro = True),
        'last_updated': Parameter(int, "Date and time when node entry was created", ro = True),
	'last_contact': Parameter(int, "Date and time when node last contacted plc", ro = True), 
        'key': Parameter(str, "(Admin only) Node key", max = 256),
        'session': Parameter(str, "(Admin only) Node session value", max = 256, ro = True),
        'interface_ids': Parameter([int], "List of network interfaces that this node has"),
        'nodegroup_ids': Parameter([int], "List of node groups that this node is in"),
        'conf_file_ids': Parameter([int], "List of configuration files specific to this node"),
        # 'root_person_ids': Parameter([int], "(Admin only) List of people who have root access to this node"),
        'slice_ids': Parameter([int], "List of slices on this node"),
	'slice_ids_whitelist': Parameter([int], "List of slices allowed on this node"),
        'pcu_ids': Parameter([int], "List of PCUs that control this node"),
        'ports': Parameter([int], "List of PCU ports that this node is connected to"),
        'peer_id': Parameter(int, "Peer to which this node belongs", nullok = True),
        'peer_node_id': Parameter(int, "Foreign node identifier at peer", nullok = True),
        'tag_ids' : Parameter ([int], "List of tags attached to this node"),
        }
    related_fields = {
	'interfaces': [Mixed(Parameter(int, "Interface identifier"),
                       	       Filter(Interface.fields))],
	'nodegroups': [Mixed(Parameter(int, "NodeGroup identifier"),
                             Parameter(str, "NodeGroup name"))],
	'conf_files': [Parameter(int, "ConfFile identifier")],
	'slices': [Mixed(Parameter(int, "Slice identifier"),
                         Parameter(str, "Slice name"))],
	'slices_whitelist': [Mixed(Parameter(int, "Slice identifier"),
                                   Parameter(str, "Slice name"))]
	}
    # for Cache
    class_key = 'hostname'
    foreign_fields = ['boot_state','model','version']
    # forget about these ones, they are read-only anyway
    # handling them causes Cache to re-sync all over again 
    # 'date_created','last_updated'
    foreign_xrefs = [
	# in this case, we dont need the 'table' but Cache will look it up, so...
        {'field' : 'site_id' , 'class' : 'Site' , 'table' : 'unused-on-direct-refs' } ,
	]

    def validate_hostname(self, hostname):
        if not valid_hostname(hostname):
            raise PLCInvalidArgument, "Invalid hostname"

        conflicts = Nodes(self.api, [hostname])
        for node in conflicts:
            if 'node_id' not in self or self['node_id'] != node['node_id']:
                raise PLCInvalidArgument, "Hostname already in use"

        return hostname

    def validate_boot_state(self, boot_state):
        boot_states = [row['boot_state'] for row in BootStates(self.api)]
        if boot_state not in boot_states:
            raise PLCInvalidArgument, "Invalid boot state"

        return boot_state

    validate_date_created = Row.validate_timestamp
    validate_last_updated = Row.validate_timestamp
    validate_last_contact = Row.validate_timestamp

    def update_last_contact(self, commit = True):
	"""
	Update last_contact field with current time
	"""
	
	assert 'node_id' in self
	assert self.table_name

	self.api.db.do("UPDATE %s SET last_contact = CURRENT_TIMESTAMP " % (self.table_name) + \
		       " where node_id = %d" % ( self['node_id']) )
	self.sync(commit)


    def update_last_updated(self, commit = True):
        """
        Update last_updated field with current time
        """

        assert 'node_id' in self
        assert self.table_name

        self.api.db.do("UPDATE %s SET last_updated = CURRENT_TIMESTAMP " % (self.table_name) + \
                       " where node_id = %d" % (self['node_id']) )
        self.sync(commit)

    def associate_interfaces(self, auth, field, value):
	"""
	Delete interfaces not found in value list (using DeleteNodeNetwor)k	
	Add interfaces found in value list (using AddInterface)
	Updates interfaces found w/ interface_id in value list (using UpdateInterface) 
	"""

	assert 'interfacep_ids' in self
        assert 'node_id' in self
        assert isinstance(value, list)

        (interface_ids, blank, interfaces) = self.separate_types(value)

        if self['interface_ids'] != interface_ids:
            from PLC.Methods.DeleteInterface import DeleteInterface

            stale_interfaces = set(self['interface_ids']).difference(interface_ids)

            for stale_interface in stale_interfaces:
                DeleteInterface.__call__(DeleteInterface(self.api), auth, stale_interface['interface_id'])

    def associate_nodegroups(self, auth, field, value):
	"""
	Add node to nodegroups found in value list (AddNodeToNodegroup)
	Delete node from nodegroup not found in value list (DeleteNodeFromNodegroup)
	"""
	
	from PLC.NodeGroups import NodeGroups
	
	assert 'nodegroup_ids' in self
	assert 'node_id' in self
	assert isinstance(value, list)

	(nodegroup_ids, nodegroup_names) = self.separate_types(value)[0:2]
	
	if nodegroup_names:
	    nodegroups = NodeGroups(self.api, nodegroup_names, ['nodegroup_id']).dict('nodegroup_id')
	    nodegroup_ids += nodegroups.keys()

	if self['nodegroup_ids'] != nodegroup_ids:
	    from PLC.Methods.AddNodeToNodeGroup import AddNodeToNodeGroup
	    from PLC.Methods.DeleteNodeFromNodeGroup import DeleteNodeFromNodeGroup
	
	    new_nodegroups = set(nodegroup_ids).difference(self['nodegroup_ids'])
	    stale_nodegroups = set(self['nodegroup_ids']).difference(nodegroup_ids)
	
	    for new_nodegroup in new_nodegroups:
		AddNodeToNodeGroup.__call__(AddNodeToNodeGroup(self.api), auth, self['node_id'], new_nodegroup)
	    for stale_nodegroup in stale_nodegroups:
		DeleteNodeFromNodeGroup.__call__(DeleteNodeFromNodeGroup(self.api), auth, self['node_id'], stale_nodegroup)
	  

 
    def associate_conf_files(self, auth, field, value):
	"""
	Add conf_files found in value list (AddConfFileToNode)
	Delets conf_files not found in value list (DeleteConfFileFromNode)
	"""
	
	assert 'conf_file_ids' in self
	assert 'node_id' in self
	assert isinstance(value, list)
	
	conf_file_ids = self.separate_types(value)[0]
	
	if self['conf_file_ids'] != conf_file_ids:
	    from PLC.Methods.AddConfFileToNode import AddConfFileToNode
	    from PLC.Methods.DeleteConfFileFromNode import DeleteConfFileFromNode
	    new_conf_files = set(conf_file_ids).difference(self['conf_file_ids'])
	    stale_conf_files = set(self['conf_file_ids']).difference(conf_file_ids)
	
	    for new_conf_file in new_conf_files:
		AddConfFileToNode.__call__(AddConfFileToNode(self.api), auth, new_conf_file, self['node_id'])
	    for stale_conf_file in stale_conf_files:
		DeleteConfFileFromNode.__call__(DeleteConfFileFromNode(self.api), auth, stale_conf_file, self['node_id'])

 
    def associate_slices(self, auth, field, value):
	"""
	Add slices found in value list to (AddSliceToNode)
	Delete slices not found in value list (DeleteSliceFromNode)
	"""
	
	from PLC.Slices import Slices
	
	assert 'slice_ids' in self
	assert 'node_id' in self
	assert isinstance(value, list)
	
	(slice_ids, slice_names) = self.separate_types(value)[0:2]

	if slice_names:
	    slices = Slices(self.api, slice_names, ['slice_id']).dict('slice_id')
	    slice_ids += slices.keys()

	if self['slice_ids'] != slice_ids:
	    from PLC.Methods.AddSliceToNodes import AddSliceToNodes
	    from PLC.Methods.DeleteSliceFromNodes import DeleteSliceFromNodes
	    new_slices = set(slice_ids).difference(self['slice_ids'])
	    stale_slices = set(self['slice_ids']).difference(slice_ids)
	
	for new_slice in new_slices:
	    AddSliceToNodes.__call__(AddSliceToNodes(self.api), auth, new_slice, [self['node_id']])
	for stale_slice in stale_slices:
	    DeleteSliceFromNodes.__call__(DeleteSliceFromNodes(self.api), auth, stale_slice, [self['node_id']]) 		 	

    def associate_slices_whitelist(self, auth, field, value):
	"""
	Add slices found in value list to whitelist (AddSliceToNodesWhitelist)
	Delete slices not found in value list from whitelist (DeleteSliceFromNodesWhitelist)
	"""

	from PLC.Slices import Slices

	assert 'slice_ids_whitelist' in self
        assert 'node_id' in self
        assert isinstance(value, list)

	(slice_ids, slice_names) = self.separate_types(value)[0:2]

        if slice_names:
            slices = Slices(self.api, slice_names, ['slice_id']).dict('slice_id')
            slice_ids += slices.keys()

        if self['slice_ids_whitelist'] != slice_ids:
            from PLC.Methods.AddSliceToNodesWhitelist import AddSliceToNodesWhitelist
            from PLC.Methods.DeleteSliceFromNodesWhitelist import DeleteSliceFromNodesWhitelist
            new_slices = set(slice_ids).difference(self['slice_ids_whitelist'])
            stale_slices = set(self['slice_ids_whitelist']).difference(slice_ids)

        for new_slice in new_slices:
            AddSliceToNodesWhitelist.__call__(AddSliceToNodesWhitelist(self.api), auth, new_slice, [self['node_id']])
        for stale_slice in stale_slices:
            DeleteSliceFromNodesWhitelist.__call__(DeleteSliceFromNodesWhitelist(self.api), auth, stale_slice, [self['node_id']]) 
		

    def delete(self, commit = True):
        """
        Delete existing node.
        """

        assert 'node_id' in self
	assert 'interface_ids' in self

	# we need to clean up InterfaceSettings, so handling interfaces as part of join_tables does not work
	for interface in Interfaces(self.api,self['interface_ids']):
	    interface.delete()

        # Clean up miscellaneous join tables
        for table in self.join_tables:
            self.api.db.do("DELETE FROM %s WHERE node_id = %d" % \
                           (table, self['node_id']))

        # Mark as deleted
        self['deleted'] = True
        self.sync(commit)


class Nodes(Table):
    """
    Representation of row(s) from the nodes table in the
    database.
    """

    def __init__(self, api, node_filter = None, columns = None):
        Table.__init__(self, api, Node, columns)

        sql = "SELECT %s FROM view_nodes WHERE deleted IS False" % \
              ", ".join(self.columns)

        if node_filter is not None:
            if isinstance(node_filter, (list, tuple, set)):
                # Separate the list into integers and strings
                ints = filter(lambda x: isinstance(x, (int, long)), node_filter)
                strs = filter(lambda x: isinstance(x, StringTypes), node_filter)
                node_filter = Filter(Node.fields, {'node_id': ints, 'hostname': strs})
                sql += " AND (%s) %s" % node_filter.sql(api, "OR")
            elif isinstance(node_filter, dict):
                node_filter = Filter(Node.fields, node_filter)
                sql += " AND (%s) %s" % node_filter.sql(api, "AND")
            elif isinstance (node_filter, StringTypes):
                node_filter = Filter(Node.fields, {'hostname':[node_filter]})
                sql += " AND (%s) %s" % node_filter.sql(api, "AND")
            elif isinstance (node_filter, int):
                node_filter = Filter(Node.fields, {'node_id':[node_filter]})
                sql += " AND (%s) %s" % node_filter.sql(api, "AND")
            else:
                raise PLCInvalidArgument, "Wrong node filter %r"%node_filter

        self.selectall(sql)
