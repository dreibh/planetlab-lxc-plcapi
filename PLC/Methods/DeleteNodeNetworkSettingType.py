#
# Thierry Parmentelat - INRIA
#
# $Revision$
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NodeNetworkSettingTypes import NodeNetworkSettingType, NodeNetworkSettingTypes
from PLC.Auth import Auth

class DeleteNodeNetworkSettingType(Method):
    """
    Deletes the specified nodenetwork setting type.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Mixed(NodeNetworkSettingType.fields['nodenetwork_setting_type_id'],
              NodeNetworkSettingType.fields['name']),
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, nodenetwork_setting_type_id_or_name):
        nodenetwork_setting_types = NodeNetworkSettingTypes(self.api, [nodenetwork_setting_type_id_or_name])
        if not nodenetwork_setting_types:
            raise PLCInvalidArgument, "No such nodenetwork setting type"
        nodenetwork_setting_type = nodenetwork_setting_types[0]

        nodenetwork_setting_type.delete()
	self.object_ids = [nodenetwork_setting_type['nodenetwork_setting_type_id']]

        return 1
