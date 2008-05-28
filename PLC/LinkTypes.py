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

class LinkType (Row):

    """
    Representation of a row in the link_types table.
    """

    table_name = 'link_types'
    primary_key = 'link_type_id'
    join_tables = ['ilink']
    fields = {
        'link_type_id': Parameter(int, "ilink type identifier"),
        'name': Parameter(str, "ilink type name", max = 100),
        'description': Parameter(str, "ilink type description", max = 254),
        'min_role_id': Parameter(int, "Minimum (least powerful) role that can set or change this attribute"),
        }

    def validate_name(self, name):
        if not len(name):
            raise PLCInvalidArgument, "ilink type name must be set"

        conflicts = LinkTypes(self.api, [name])
        for tag_type in conflicts:
            if 'link_type_id' not in self or \
                   self['link_type_id'] != tag_type['link_type_id']:
                raise PLCInvalidArgument, "ilink type name already in use"

        return name

    def validate_min_role_id(self, role_id):
        roles = [row['role_id'] for row in Roles(self.api)]
        if role_id not in roles:
            raise PLCInvalidArgument, "Invalid role"

        return role_id

class LinkTypes(Table):
    """
    Representation of row(s) from the link_types table
    in the database.
    """

    def __init__(self, api, link_type_filter = None, columns = None):
        Table.__init__(self, api, LinkType, columns)

        sql = "SELECT %s FROM link_types WHERE True" % \
              ", ".join(self.columns)

        if link_type_filter is not None:
            if isinstance(link_type_filter, (list, tuple, set)):
                # Separate the list into integers and strings
                ints = filter(lambda x: isinstance(x, (int, long)), link_type_filter)
                strs = filter(lambda x: isinstance(x, StringTypes), link_type_filter)
                link_type_filter = Filter(LinkType.fields, {'link_type_id': ints, 'name': strs})
                sql += " AND (%s) %s" % link_type_filter.sql(api, "OR")
            elif isinstance(link_type_filter, dict):
                link_type_filter = Filter(LinkType.fields, link_type_filter)
                sql += " AND (%s) %s" % link_type_filter.sql(api, "AND")
            elif isinstance (link_type_filter, StringTypes):
                link_type_filter = Filter(LinkType.fields, {'name':[link_type_filter]})
                sql += " AND (%s) %s" % link_type_filter.sql(api, "AND")
            else:
                raise PLCInvalidArgument, "Wrong ilink type filter %r"%link_type_filter

        self.selectall(sql)
