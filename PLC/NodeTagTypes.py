#
# Thierry Parmentelat - INRIA
#
# $Revision: 9423 $
#
from types import StringTypes

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Table import Row, Table
from PLC.Roles import Role, Roles

class NodeTagType (Row):

    """
    Representation of a row in the node_tag_types table.
    """

    table_name = 'node_tag_types'
    primary_key = 'node_tag_type_id'
    join_tables = ['node_tag']
    fields = {
        'node_tag_type_id': Parameter(int, "Node tag type identifier"),
        'tagname': Parameter(str, "Node tag type name", max = 100),
        'description': Parameter(str, "Node tag type description", max = 254),
        'category' : Parameter (str, "Node tag category", max=64, optional=True),
        'min_role_id': Parameter(int, "Minimum (least powerful) role that can set or change this attribute"),
        }

    def validate_name(self, name):
        if not len(name):
            raise PLCInvalidArgument, "node tag type name must be set"

        conflicts = NodeTagTypes(self.api, [name])
        for tag_type in conflicts:
            if 'node_tag_type_id' not in self or \
                   self['node_tag_type_id'] != tag_type['node_tag_type_id']:
                raise PLCInvalidArgument, "node tag type name already in use"

        return name

    def validate_min_role_id(self, role_id):
        roles = [row['role_id'] for row in Roles(self.api)]
        if role_id not in roles:
            raise PLCInvalidArgument, "Invalid role"

        return role_id

class NodeTagTypes(Table):
    """
    Representation of row(s) from the node_tag_types table
    in the database.
    """

    def __init__(self, api, node_tag_type_filter = None, columns = None):
        Table.__init__(self, api, NodeTagType, columns)

        sql = "SELECT %s FROM node_tag_types WHERE True" % \
              ", ".join(self.columns)

        if node_tag_type_filter is not None:
            if isinstance(node_tag_type_filter, (list, tuple, set)):
                # Separate the list into integers and strings
                ints = filter(lambda x: isinstance(x, (int, long)), node_tag_type_filter)
                strs = filter(lambda x: isinstance(x, StringTypes), node_tag_type_filter)
                node_tag_type_filter = Filter(NodeTagType.fields, {'node_tag_type_id': ints, 'tagname': strs})
                sql += " AND (%s) %s" % node_tag_type_filter.sql(api, "OR")
            elif isinstance(node_tag_type_filter, dict):
                node_tag_type_filter = Filter(NodeTagType.fields, node_tag_type_filter)
                sql += " AND (%s) %s" % node_tag_type_filter.sql(api, "AND")
            elif isinstance (node_tag_type_filter, StringTypes):
                node_tag_type_filter = Filter(NodeTagType.fields, {'tagname':[node_tag_type_filter]})
                sql += " AND (%s) %s" % node_tag_type_filter.sql(api, "AND")
            else:
                raise PLCInvalidArgument, "Wrong node tag type filter %r"%node_tag_type_filter

        self.selectall(sql)
