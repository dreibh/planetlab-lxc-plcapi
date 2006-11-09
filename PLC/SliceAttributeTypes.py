from types import StringTypes

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Table import Row, Table
from PLC.Roles import Role, Roles

class SliceAttributeType(Row):
    """
    Representation of a row in the slice_attribute_types table. To
    use, instantiate with a dict of values.
    """

    table_name = 'slice_attribute_types'
    primary_key = 'attribute_type_id'
    join_tables = ['slice_attribute']
    fields = {
        'attribute_type_id': Parameter(int, "Slice attribute type identifier"),
        'name': Parameter(str, "Slice attribute type name", max = 100),
        'description': Parameter(str, "Slice attribute type description", max = 254),
        'min_role_id': Parameter(int, "Minimum (least powerful) role that can set or change this attribute"),
        }

    def validate_name(self, name):
        if not len(name):
            raise PLCInvalidArgument, "Slice attribute type name must be set"

        conflicts = SliceAttributeTypes(self.api, [name])
        for attribute_type_id, attribute in conflicts.iteritems():
            if 'attribute_type_id' not in self or self['attribute_type_id'] != attribute_type_id:
                raise PLCInvalidArgument, "Slice attribute type name already in use"

        return name

    def validate_min_role_id(self, role_id):
        roles = Roles(self.api)
        if role_id not in roles:
            raise PLCInvalidArgument, "Invalid role"

        return role_id

class SliceAttributeTypes(Table):
    """
    Representation of row(s) from the slice_attribute_types table in the
    database.
    """

    def __init__(self, api, attribute_type_filter = None):
        Table.__init__(self, api, SliceAttributeType)

        sql = "SELECT %s FROM slice_attribute_types WHERE True" % \
              ", ".join(SliceAttributeType.fields)

        if attribute_type_filter is not None:
            if isinstance(attribute_type_filter, (list, tuple, set)):
                # Separate the list into integers and strings
                ints = filter(lambda x: isinstance(x, (int, long)), attribute_type_filter)
                strs = filter(lambda x: isinstance(x, StringTypes), attribute_type_filter)
                attribute_type_filter = Filter(SliceAttributeType.fields, {'attribute_type_id': ints, 'name': strs})
                sql += " AND (%s)" % attribute_type_filter.sql(api, "OR")
            elif isinstance(attribute_type_filter, dict):
                attribute_type_filter = Filter(SliceAttributeType.fields, attribute_type_filter)
                sql += " AND (%s)" % attribute_type_filter.sql(api, "AND")

        self.selectall(sql)
