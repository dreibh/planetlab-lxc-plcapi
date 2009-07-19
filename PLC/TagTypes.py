# $Id$
# $URL$
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

# xxx todo : deleting a tag type should delete the related nodegroup(s)

class TagType (Row):

    """
    Representation of a row in the tag_types table.
    """

    table_name = 'tag_types'
    primary_key = 'tag_type_id'
    join_tables = ['node_tag', 'interface_tag', 'slice_tag' ]
    fields = {
        'tag_type_id': Parameter(int, "Node tag type identifier"),
        'tagname': Parameter(str, "Node tag type name", max = 100),
        'description': Parameter(str, "Node tag type description", max = 254),
        'category' : Parameter (str, "Node tag category", max=64, optional=True),
        'min_role_id': Parameter(int, "Minimum (least powerful) role that can set or change this attribute"),
        }

    def validate_name(self, name):
        if not len(name):
            raise PLCInvalidArgument, "node tag type name must be set"

        conflicts = TagTypes(self.api, [name])
        for tag_type in conflicts:
            if 'tag_type_id' not in self or \
                   self['tag_type_id'] != tag_type['tag_type_id']:
                raise PLCInvalidArgument, "node tag type name already in use"

        return name

    def validate_min_role_id(self, role_id):
        roles = [row['role_id'] for row in Roles(self.api)]
        if role_id not in roles:
            raise PLCInvalidArgument, "Invalid role"

        return role_id

class TagTypes(Table):
    """
    Representation of row(s) from the tag_types table
    in the database.
    """

    def __init__(self, api, tag_type_filter = None, columns = None):
        Table.__init__(self, api, TagType, columns)

        sql = "SELECT %s FROM tag_types WHERE True" % \
              ", ".join(self.columns)

        if tag_type_filter is not None:
            if isinstance(tag_type_filter, (list, tuple, set)):
                # Separate the list into integers and strings
                ints = filter(lambda x: isinstance(x, (int, long)), tag_type_filter)
                strs = filter(lambda x: isinstance(x, StringTypes), tag_type_filter)
                tag_type_filter = Filter(TagType.fields, {'tag_type_id': ints, 'tagname': strs})
                sql += " AND (%s) %s" % tag_type_filter.sql(api, "OR")
            elif isinstance(tag_type_filter, dict):
                tag_type_filter = Filter(TagType.fields, tag_type_filter)
                sql += " AND (%s) %s" % tag_type_filter.sql(api, "AND")
            elif isinstance (tag_type_filter, StringTypes):
                tag_type_filter = Filter(TagType.fields, {'tagname':[tag_type_filter]})
                sql += " AND (%s) %s" % tag_type_filter.sql(api, "AND")
            else:
                raise PLCInvalidArgument, "Wrong node tag type filter %r"%tag_type_filter

        self.selectall(sql)
