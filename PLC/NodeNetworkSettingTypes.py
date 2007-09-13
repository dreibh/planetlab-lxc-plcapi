#
# Thierry Parmentelat - INRIA
#
# $Revision:$
#
from types import StringTypes

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Table import Row, Table
from PLC.Roles import Role, Roles

class NodeNetworkSettingType (Row):

    """
    Representation of a row in the nodenetwork_setting_types table.
    """

    table_name = 'nodenetwork_setting_types'
    primary_key = 'nodenetwork_setting_type_id'
    join_tables = ['nodenetwork_setting']
    fields = {
        'nodenetwork_setting_type_id': Parameter(int, "Nodenetwork setting type identifier"),
        'name': Parameter(str, "Nodenetwork setting type name", max = 100),
        'description': Parameter(str, "Nodenetwork setting type description", max = 254),
        'category' : Parameter (str, "Nodenetwork setting category", max=64),
        'min_role_id': Parameter(int, "Minimum (least powerful) role that can set or change this attribute"),
        }

    # for Cache
    class_key = 'name'
    foreign_fields = ['category','description','min_role_id']
    foreign_xrefs = []

    def validate_name(self, name):
        if not len(name):
            raise PLCInvalidArgument, "nodenetwork setting type name must be set"

        conflicts = NodeNetworkSettingTypes(self.api, [name])
        for setting_type in conflicts:
            if 'nodenetwork_setting_type_id' not in self or \
                   self['nodenetwork_setting_type_id'] != setting_type['nodenetwork_setting_type_id']:
                raise PLCInvalidArgument, "nodenetwork setting type name already in use"

        return name

    def validate_min_role_id(self, role_id):
        roles = [row['role_id'] for row in Roles(self.api)]
        if role_id not in roles:
            raise PLCInvalidArgument, "Invalid role"

        return role_id

class NodeNetworkSettingTypes(Table):
    """
    Representation of row(s) from the nodenetwork_setting_types table
    in the database.
    """

    def __init__(self, api, nodenetwork_setting_type_filter = None, columns = None):
        Table.__init__(self, api, NodeNetworkSettingType, columns)

        sql = "SELECT %s FROM nodenetwork_setting_types WHERE True" % \
              ", ".join(self.columns)

        if nodenetwork_setting_type_filter is not None:
            if isinstance(nodenetwork_setting_type_filter, (list, tuple, set)):
                # Separate the list into integers and strings
                ints = filter(lambda x: isinstance(x, (int, long)), nodenetwork_setting_type_filter)
                strs = filter(lambda x: isinstance(x, StringTypes), nodenetwork_setting_type_filter)
                nodenetwork_setting_type_filter = Filter(NodeNetworkSettingType.fields, {'nodenetwork_setting_type_id': ints, 'name': strs})
                sql += " AND (%s)" % nodenetwork_setting_type_filter.sql(api, "OR")
            elif isinstance(nodenetwork_setting_type_filter, dict):
                nodenetwork_setting_type_filter = Filter(NodeNetworkSettingType.fields, nodenetwork_setting_type_filter)
                sql += " AND (%s)" % nodenetwork_setting_type_filter.sql(api, "AND")
            elif isinstance (nodenetwork_setting_type_filter, StringTypes):
                nodenetwork_setting_type_filter = Filter(NodeNetworkSettingType.fields, {'name':[nodenetwork_setting_type_filter]})
                sql += " AND (%s)" % nodenetwork_setting_type_filter.sql(api, "AND")
            else:
                raise PLCInvalidArgument, "Wrong nodenetwork setting type filter %r"%nodenetwork_setting_type_filter

        self.selectall(sql)
