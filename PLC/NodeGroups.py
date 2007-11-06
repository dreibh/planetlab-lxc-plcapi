#
# Functions for interacting with the nodegroups table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id$
#

from types import StringTypes

from PLC.Faults import *
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Debug import profile
from PLC.Table import Row, Table
from PLC.Nodes import Node, Nodes

class NodeGroup(Row):
    """
    Representation of a row in the nodegroups table. To use, optionally
    instantiate with a dict of values. Update as you would a
    dict. Commit to the database with sync().
    """

    table_name = 'nodegroups'
    primary_key = 'nodegroup_id'
    join_tables = ['nodegroup_node', 'conf_file_nodegroup']
    fields = {
        'nodegroup_id': Parameter(int, "Node group identifier"),
        'name': Parameter(str, "Node group name", max = 50),
        'description': Parameter(str, "Node group description", max = 200, nullok = True),
        'node_ids': Parameter([int], "List of nodes in this node group"),
        'conf_file_ids': Parameter([int], "List of configuration files specific to this node group"),
        }
    related_fields = {
	'conf_files': [Parameter(int, "ConfFile identifier")],
	'nodes': [Mixed(Parameter(int, "Node identifier"),
                        Parameter(str, "Fully qualified hostname"))]
	}

    def validate_name(self, name):
	# Make sure name is not blank
        if not len(name):
                raise PLCInvalidArgument, "Invalid node group name"
	
	# Make sure node group does not alredy exist
	conflicts = NodeGroups(self.api, [name])
	for nodegroup in conflicts:
            if 'nodegroup_id' not in self or self['nodegroup_id'] != nodegroup['nodegroup_id']:
               raise PLCInvalidArgument, "Node group name already in use"

	return name

    def add_node(self, node, commit = True):
        """
        Add node to existing nodegroup.
        """

        assert 'nodegroup_id' in self
        assert isinstance(node, Node)
        assert 'node_id' in node

        node_id = node['node_id']
        nodegroup_id = self['nodegroup_id']

        if node_id not in self['node_ids']:
            assert nodegroup_id not in node['nodegroup_ids']

            self.api.db.do("INSERT INTO nodegroup_node (nodegroup_id, node_id)" \
                           " VALUES(%(nodegroup_id)d, %(node_id)d)",
                           locals())

            if commit:
                self.api.db.commit()

            self['node_ids'].append(node_id)
            node['nodegroup_ids'].append(nodegroup_id)

    def remove_node(self, node, commit = True):
        """
        Remove node from existing nodegroup.
        """

        assert 'nodegroup_id' in self
        assert isinstance(node, Node)
        assert 'node_id' in node

        node_id = node['node_id']
        nodegroup_id = self['nodegroup_id']

        if node_id in self['node_ids']:
            assert nodegroup_id in node['nodegroup_ids']

            self.api.db.do("DELETE FROM nodegroup_node" \
                           " WHERE nodegroup_id = %(nodegroup_id)d" \
                           " AND node_id = %(node_id)d",
                           locals())

            if commit:
                self.api.db.commit()

            self['node_ids'].remove(node_id)
            node['nodegroup_ids'].remove(nodegroup_id)

    def associate_nodes(self, auth, field, value):
        """
        Adds nodes found in value list to this nodegroup (using AddNodeToNodeGroup).
        Deletes nodes not found in value list from this slice (using DeleteNodeFromNodeGroup).
        """

        assert 'node_ids' in self
        assert 'nodegroup_id' in self
        assert isinstance(value, list)

        (node_ids, hostnames) = self.separate_types(value)[0:2]

        # Translate hostnames into node_ids
        if hostnames:
            nodes = Nodes(self.api, hostnames, ['node_id']).dict('node_id')
            node_ids += nodes.keys()

        # Add new ids, remove stale ids
        if self['node_ids'] != node_ids:
            from PLC.Methods.AddNodeToNodeGroup import AddNodeToNodeGroup
            from PLC.Methods.DeleteNodeFromNodeGroup import DeleteNodeFromNodeGroup
            new_nodes = set(node_ids).difference(self['node_ids'])
            stale_nodes = set(self['node_ids']).difference(node_ids)

            for new_node in new_nodes:
                AddNodeToNodeGroup.__call__(AddNodeToNodeGroup(self.api), auth, new_node, self['nodegroup_id'])
            for stale_node in stale_nodes:
                DeleteNodeFromNodeGroup.__call__(DeleteNodeFromNodeGroup(self.api), auth, stale_node, self['nodegroup_id'])

    def associate_conf_files(self, auth, field, value):
        """
        Add conf_files found in value list (AddConfFileToNodeGroup)
        Delets conf_files not found in value list (DeleteConfFileFromNodeGroup)
        """

        assert 'conf_file_ids' in self
        assert 'nodegroup_id' in self
        assert isinstance(value, list)

        conf_file_ids = self.separate_types(value)[0]

        if self['conf_file_ids'] != conf_file_ids:
            from PLC.Methods.AddConfFileToNodeGroup import AddConfFileToNodeGroup
            from PLC.Methods.DeleteConfFileFromNodeGroup import DeleteConfFileFromNodeGroup
            new_conf_files = set(conf_file_ids).difference(self['conf_file_ids'])
            stale_conf_files = set(self['conf_file_ids']).difference(conf_file_ids)

            for new_conf_file in new_conf_files:
                AddConfFileToNodeGroup.__call__(AddConfFileToNodeGroup(self.api), auth, new_conf_file, self['nodegroup_id'])
            for stale_conf_file in stale_conf_files:
                DeleteConfFileFromNodeGroup.__call__(DeleteConfFileFromNodeGroup(self.api), auth, stale_conf_file, self['nodegroup_id'])


class NodeGroups(Table):
    """
    Representation of row(s) from the nodegroups table in the
    database.
    """

    def __init__(self, api, nodegroup_filter = None, columns = None):
        Table.__init__(self, api, NodeGroup, columns)

        sql = "SELECT %s FROM view_nodegroups WHERE True" % \
              ", ".join(self.columns)

        if nodegroup_filter is not None:
            if isinstance(nodegroup_filter, (list, tuple, set)):
                # Separate the list into integers and strings
                ints = filter(lambda x: isinstance(x, (int, long)), nodegroup_filter)
                strs = filter(lambda x: isinstance(x, StringTypes), nodegroup_filter)
                nodegroup_filter = Filter(NodeGroup.fields, {'nodegroup_id': ints, 'name': strs})
                sql += " AND (%s) %s" % nodegroup_filter.sql(api, "OR")
            elif isinstance(nodegroup_filter, dict):
                nodegroup_filter = Filter(NodeGroup.fields, nodegroup_filter)
                sql += " AND (%s) %s" % nodegroup_filter.sql(api, "AND")

        self.selectall(sql)
