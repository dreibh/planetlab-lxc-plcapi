#
# Thierry Parmentelat - INRIA
#
# $Revision$
#
from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Table import Row, Table
from PLC.InterfaceSettingTypes import InterfaceSettingType, InterfaceSettingTypes

class InterfaceSetting(Row):
    """
    Representation of a row in the interface_setting.
    To use, instantiate with a dict of values.
    """

    table_name = 'interface_setting'
    primary_key = 'interface_setting_id'
    fields = {
        'interface_setting_id': Parameter(int, "Interface setting identifier"),
        'interface_id': Parameter(int, "Interface identifier"),
        'interface_setting_type_id': InterfaceSettingType.fields['interface_setting_type_id'],
        'name': InterfaceSettingType.fields['name'],
        'description': InterfaceSettingType.fields['description'],
        'category': InterfaceSettingType.fields['category'],
        'min_role_id': InterfaceSettingType.fields['min_role_id'],
        'value': Parameter(str, "Interface setting value"),
	### relations
	
        }

class InterfaceSettings(Table):
    """
    Representation of row(s) from the interface_setting table in the
    database.
    """

    def __init__(self, api, interface_setting_filter = None, columns = None):
        Table.__init__(self, api, InterfaceSetting, columns)

        sql = "SELECT %s FROM view_interface_settings WHERE True" % \
              ", ".join(self.columns)

        if interface_setting_filter is not None:
            if isinstance(interface_setting_filter, (list, tuple, set)):
                interface_setting_filter = Filter(InterfaceSetting.fields, {'interface_setting_id': interface_setting_filter})
            elif isinstance(interface_setting_filter, dict):
                interface_setting_filter = Filter(InterfaceSetting.fields, interface_setting_filter)
            elif isinstance(interface_setting_filter, int):
                interface_setting_filter = Filter(InterfaceSetting.fields, {'interface_setting_id': [interface_setting_filter]})
            else:
                raise PLCInvalidArgument, "Wrong interface setting filter %r"%interface_setting_filter
            sql += " AND (%s) %s" % interface_setting_filter.sql(api)


        self.selectall(sql)
