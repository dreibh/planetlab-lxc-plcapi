#
# Thierry Parmentelat - INRIA
#
# $Revision: 88 $
#
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.NodeNetworkSettingTypes import NodeNetworkSettingType, NodeNetworkSettingTypes

class GetNodeNetworkSettingTypes(Method):
    """
    Returns an array of structs containing details about
    nodenetwork setting types.

    The usual filtering scheme applies on this method.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node']

    accepts = [
        Auth(),
        Mixed([Mixed(NodeNetworkSettingType.fields['nodenetwork_setting_type_id'],
                     NodeNetworkSettingType.fields['name'])],
              Filter(NodeNetworkSettingType.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [NodeNetworkSettingType.fields]

    def call(self, auth, nodenetwork_setting_type_filter = None, return_fields = None):
        return NodeNetworkSettingTypes(self.api, nodenetwork_setting_type_filter, return_fields)
