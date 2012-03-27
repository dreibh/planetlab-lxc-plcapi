#
# Functions for interacting with the nodegroups table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
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
    join_tables = ['conf_file_nodegroup']
    primary_field = 'nodegroup_id'
    fields = {
        'nodegroup_id': Parameter(int, "Node group identifier"),
        'groupname': Parameter(str, "Node group name", max = 50),
        'tag_type_id': Parameter (int, "Node tag type id"),
        'value' : Parameter(str, "value that the nodegroup definition is based upon"),
        'tagname' : Parameter(str, "Tag name that the nodegroup definition is based upon"),
        'conf_file_ids': Parameter([int], "List of configuration files specific to this node group"),
        'node_ids' : Parameter([int], "List of node_ids that belong to this nodegroup"),
        }
    related_fields = {
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
                AddConfFileToNodeGroup.__call__(AddConfFileToNodeGroup(self.api),
                                                auth, new_conf_file, self['nodegroup_id'])
            for stale_conf_file in stale_conf_files:
                DeleteConfFileFromNodeGroup.__call__(DeleteConfFileFromNodeGroup(self.api),
                                                     auth, stale_conf_file, self['nodegroup_id'])


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
                nodegroup_filter = Filter(NodeGroup.fields, {'nodegroup_id': ints, 'groupname': strs})
                sql += " AND (%s) %s" % nodegroup_filter.sql(api, "OR")
            elif isinstance(nodegroup_filter, dict):
                nodegroup_filter = Filter(NodeGroup.fields, nodegroup_filter)
                sql += " AND (%s) %s" % nodegroup_filter.sql(api, "AND")
            elif isinstance(nodegroup_filter, (int, long)):
                nodegroup_filter = Filter(NodeGroup.fields, {'nodegroup_id': nodegroup_filter})
                sql += " AND (%s) %s" % nodegroup_filter.sql(api, "AND")
            elif isinstance(nodegroup_filter, StringTypes):
                nodegroup_filter = Filter(NodeGroup.fields, {'groupname': nodegroup_filter})
                sql += " AND (%s) %s" % nodegroup_filter.sql(api, "AND")
            else:
                raise PLCInvalidArgument, "Wrong node group filter %r"%nodegroup_filter

        self.selectall(sql)
