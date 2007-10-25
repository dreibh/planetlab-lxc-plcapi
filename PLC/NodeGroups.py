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
from PLC.Parameter import Parameter
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

    def validate_name(self, name):
	# Make sure name is not blank
        if not len(name):
                raise PLCInvalidArgument, "Invalid node group name"
	
	# Make sure node group does not alredy exist
	conflicts = NodeGroups(self.api, [name])
	for nodegroup_id in conflicts:
            if 'nodegroup_id' not in self or self['nodegroup_id'] != nodegroup_id:
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
