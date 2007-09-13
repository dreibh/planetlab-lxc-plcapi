#
# Thierry Parmentelat - INRIA
#
# $Revision$
#
from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Table import Row, Table
from PLC.NodeNetworkSettingTypes import NodeNetworkSettingType, NodeNetworkSettingTypes

class NodeNetworkSetting(Row):
    """
    Representation of a row in the nodenetwork_setting.
    To use, instantiate with a dict of values.
    """

    table_name = 'nodenetwork_setting'
    primary_key = 'nodenetwork_setting_id'
    fields = {
        'nodenetwork_setting_id': Parameter(int, "Nodenetwork setting identifier"),
        'nodenetwork_id': Parameter(int, "NodeNetwork identifier"),
        'nodenetwork_setting_type_id': NodeNetworkSettingType.fields['nodenetwork_setting_type_id'],
        'name': NodeNetworkSettingType.fields['name'],
        'description': NodeNetworkSettingType.fields['description'],
        'category': NodeNetworkSettingType.fields['category'],
        'min_role_id': NodeNetworkSettingType.fields['min_role_id'],
        'value': Parameter(str, "Nodenetwork setting value"),
	### relations
	
        }

class NodeNetworkSettings(Table):
    """
    Representation of row(s) from the nodenetwork_setting table in the
    database.
    """

    def __init__(self, api, nodenetwork_setting_filter = None, columns = None):
        Table.__init__(self, api, NodeNetworkSetting, columns)

        sql = "SELECT %s FROM view_nodenetwork_settings WHERE True" % \
              ", ".join(self.columns)

        if nodenetwork_setting_filter is not None:
            if isinstance(nodenetwork_setting_filter, (list, tuple, set)):
                nodenetwork_setting_filter = Filter(NodeNetworkSetting.fields, {'nodenetwork_setting_id': nodenetwork_setting_filter})
            elif isinstance(nodenetwork_setting_filter, dict):
                nodenetwork_setting_filter = Filter(NodeNetworkSetting.fields, nodenetwork_setting_filter)
            elif isinstance(nodenetwork_setting_filter, int):
                nodenetwork_setting_filter = Filter(NodeNetworkSetting.fields, {'nodenetwork_setting_id': [nodenetwork_setting_filter]})
            else:
                raise PLCInvalidArgument, "Wrong nodenetwork setting filter %r"%nodenetwork_setting_filter
            sql += " AND (%s)" % nodenetwork_setting_filter.sql(api)


        self.selectall(sql)
