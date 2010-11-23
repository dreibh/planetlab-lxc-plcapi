#
# Thierry Parmentelat - INRIA
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
    join_tables = ['tag_type_role', 'node_tag', 'interface_tag', 'slice_tag', 'site_tag', 'person_tag' ]
    fields = {
        'tag_type_id': Parameter(int, "Node tag type identifier"),
        'tagname': Parameter(str, "Node tag type name", max = 100),
        'description': Parameter(str, "Node tag type description", max = 254),
        'category' : Parameter (str, "Node tag category", max=64, optional=True),
        'role_ids': Parameter([int], "List of role identifiers"),
        'roles': Parameter([str], "List of roles"),
        }

    def validate_name(self, name):
        if not len(name):
            raise PLCInvalidArgument, "tag type name must be set"

        conflicts = TagTypes(self.api, [name])
        for tag_type in conflicts:
            if 'tag_type_id' not in self or \
                   self['tag_type_id'] != tag_type['tag_type_id']:
                raise PLCInvalidArgument, "tag type name already in use"

        return name

    add_role = Row.add_object(Role, 'tag_type_role')
    remove_role = Row.remove_object(Role, 'tag_type_role')


class TagTypes(Table):
    """
    Representation of row(s) from the tag_types table
    in the database.
    """

    def __init__(self, api, tag_type_filter = None, columns = None):
        Table.__init__(self, api, TagType, columns)

        sql = "SELECT %s FROM view_tag_types WHERE True" % \
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
            elif isinstance(tag_type_filter, (int, long)):
                tag_type_filter = Filter(TagType.fields, {'tag_type_id':tag_type_filter})
                sql += " AND (%s) %s" % tag_type_filter.sql(api, "AND")
            elif isinstance(tag_type_filter, StringTypes):
                tag_type_filter = Filter(TagType.fields, {'tagname':tag_type_filter})
                sql += " AND (%s) %s" % tag_type_filter.sql(api, "AND")
            else:
                raise PLCInvalidArgument, "Wrong tag type filter %r"%tag_type_filter

        self.selectall(sql)
