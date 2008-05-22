#
# Thierry Parmentelat - INRIA
#
# $Revision$
#
from types import StringTypes

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Table import Row, Table
from PLC.Roles import Role, Roles

class InterfaceSettingType (Row):

    """
    Representation of a row in the interface_setting_types table.
    """

    table_name = 'interface_setting_types'
    primary_key = 'interface_setting_type_id'
    join_tables = ['interface_setting']
    fields = {
        'interface_setting_type_id': Parameter(int, "Interface setting type identifier"),
        'name': Parameter(str, "Interface setting type name", max = 100),
        'description': Parameter(str, "Interface setting type description", max = 254),
        'category' : Parameter (str, "Interface setting category", max=64),
        'min_role_id': Parameter(int, "Minimum (least powerful) role that can set or change this attribute"),
        }

    # for Cache
    class_key = 'name'
    foreign_fields = ['category','description','min_role_id']
    foreign_xrefs = []

    def validate_name(self, name):
        if not len(name):
            raise PLCInvalidArgument, "interface setting type name must be set"

        conflicts = InterfaceSettingTypes(self.api, [name])
        for setting_type in conflicts:
            if 'interface_setting_type_id' not in self or \
                   self['interface_setting_type_id'] != setting_type['interface_setting_type_id']:
                raise PLCInvalidArgument, "interface setting type name already in use"

        return name

    def validate_min_role_id(self, role_id):
        roles = [row['role_id'] for row in Roles(self.api)]
        if role_id not in roles:
            raise PLCInvalidArgument, "Invalid role"

        return role_id

class InterfaceSettingTypes(Table):
    """
    Representation of row(s) from the interface_setting_types table
    in the database.
    """

    def __init__(self, api, interface_setting_type_filter = None, columns = None):
        Table.__init__(self, api, InterfaceSettingType, columns)

        sql = "SELECT %s FROM interface_setting_types WHERE True" % \
              ", ".join(self.columns)

        if interface_setting_type_filter is not None:
            if isinstance(interface_setting_type_filter, (list, tuple, set)):
                # Separate the list into integers and strings
                ints = filter(lambda x: isinstance(x, (int, long)), interface_setting_type_filter)
                strs = filter(lambda x: isinstance(x, StringTypes), interface_setting_type_filter)
                interface_setting_type_filter = Filter(InterfaceSettingType.fields, {'interface_setting_type_id': ints, 'name': strs})
                sql += " AND (%s) %s" % interface_setting_type_filter.sql(api, "OR")
            elif isinstance(interface_setting_type_filter, dict):
                interface_setting_type_filter = Filter(InterfaceSettingType.fields, interface_setting_type_filter)
                sql += " AND (%s) %s" % interface_setting_type_filter.sql(api, "AND")
            elif isinstance (interface_setting_type_filter, StringTypes):
                interface_setting_type_filter = Filter(InterfaceSettingType.fields, {'name':[interface_setting_type_filter]})
                sql += " AND (%s) %s" % interface_setting_type_filter.sql(api, "AND")
            else:
                raise PLCInvalidArgument, "Wrong interface setting type filter %r"%interface_setting_type_filter

        self.selectall(sql)
