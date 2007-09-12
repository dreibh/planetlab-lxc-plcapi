#
# Thierry Parmentelat - INRIA
#
# $Revision: 88 $
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NodeNetworkSettingTypes import NodeNetworkSettingType, NodeNetworkSettingTypes
from PLC.Auth import Auth

can_update = lambda (field, value): field in \
             ['name', 'description', 'category', 'min_role_id']

class UpdateNodeNetworkSettingType(Method):
    """
    Updates the parameters of an existing setting type
    with the values in nodenetwork_setting_type_fields.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    nodenetwork_setting_type_fields = dict(filter(can_update, NodeNetworkSettingType.fields.items()))

    accepts = [
        Auth(),
        Mixed(NodeNetworkSettingType.fields['nodenetwork_setting_type_id'],
              NodeNetworkSettingType.fields['name']),
        nodenetwork_setting_type_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, nodenetwork_setting_type_id_or_name, nodenetwork_setting_type_fields):
        nodenetwork_setting_type_fields = dict(filter(can_update, nodenetwork_setting_type_fields.items()))

        nodenetwork_setting_types = NodeNetworkSettingTypes(self.api, [nodenetwork_setting_type_id_or_name])
        if not nodenetwork_setting_types:
            raise PLCInvalidArgument, "No such setting type"
        nodenetwork_setting_type = nodenetwork_setting_types[0]

        nodenetwork_setting_type.update(nodenetwork_setting_type_fields)
        nodenetwork_setting_type.sync()
	self.object_ids = [nodenetwork_setting_type['nodenetwork_setting_type_id']]

        return 1
