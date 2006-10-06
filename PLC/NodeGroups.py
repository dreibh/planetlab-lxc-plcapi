#
# Functions for interacting with the nodegroups table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: NodeGroups.py,v 1.11 2006/10/03 19:25:30 mlhuang Exp $
#

from types import StringTypes

from PLC.Faults import *
from PLC.Parameter import Parameter
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
    fields = {
        'nodegroup_id': Parameter(int, "Node group identifier"),
        'name': Parameter(str, "Node group name", max = 50),
        'description': Parameter(str, "Node group description", max = 200),
        'node_ids': Parameter([int], "List of nodes in this node group"),
        }

    def __init__(self, api, fields = {}):
        Row.__init__(self, fields)
        self.api = api

    def validate_name(self, name):
	# Remove leading and trailing spaces
	name = name.strip()

	# Make sure name is not blank after we removed the spaces
        if not len(name) > 0:
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

    def delete(self, commit = True):
        """
        Delete existing nodegroup from the database.
        """

        assert 'nodegroup_id' in self

        # Clean up miscellaneous join tables
        for table in ['nodegroup_node', 'nodegroups']:
            self.api.db.do("DELETE FROM %s" \
                           " WHERE nodegroup_id = %d" % \
                           (table, self['nodegroup_id']), self)

        if commit:
            self.api.db.commit()

class NodeGroups(Table):
    """
    Representation of row(s) from the nodegroups table in the
    database.
    """

    def __init__(self, api, nodegroup_id_or_name_list = None):
	self.api = api

        sql = "SELECT %s FROM view_nodegroups" % \
              ", ".join(NodeGroup.fields)

        if nodegroup_id_or_name_list:
            # Separate the list into integers and strings
            nodegroup_ids = filter(lambda nodegroup_id: isinstance(nodegroup_id, (int, long)),
                                   nodegroup_id_or_name_list)
            names = filter(lambda name: isinstance(name, StringTypes),
                           nodegroup_id_or_name_list)
            sql += " WHERE (False"
            if nodegroup_ids:
                sql += " OR nodegroup_id IN (%s)" % ", ".join(map(str, nodegroup_ids))
            if names:
                sql += " OR name IN (%s)" % ", ".join(api.db.quote(names))
            sql += ")"

        rows = self.api.db.selectall(sql)

        for row in rows:
            self[row['nodegroup_id']] = nodegroup = NodeGroup(api, row)
            for aggregate in ['node_ids']:
                if not nodegroup.has_key(aggregate) or nodegroup[aggregate] is None:
                    nodegroup[aggregate] = []
                else:
                    nodegroup[aggregate] = map(int, nodegroup[aggregate].split(','))
