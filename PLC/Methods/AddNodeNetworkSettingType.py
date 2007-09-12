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

class AddNodeNetworkSettingType(Method):
    """
    Adds a new type of nodenetwork setting.
    Any fields specified are used, otherwise defaults are used.

    Returns the new nodenetwork_setting_id (> 0) if successful,
    faults otherwise.
    """

    roles = ['admin']

    nodenetwork_setting_type_fields = dict(filter(can_update, NodeNetworkSettingType.fields.items()))

    accepts = [
        Auth(),
        nodenetwork_setting_type_fields
        ]

    returns = Parameter(int, 'New nodenetwork_setting_id (> 0) if successful')


    def call(self, auth, nodenetwork_setting_type_fields):
        nodenetwork_setting_type_fields = dict(filter(can_update, nodenetwork_setting_type_fields.items()))
        nodenetwork_setting_type = NodeNetworkSettingType(self.api, nodenetwork_setting_type_fields)
        nodenetwork_setting_type.sync()

	self.object_ids = [nodenetwork_setting_type['nodenetwork_setting_type_id']]

        return nodenetwork_setting_type['nodenetwork_setting_type_id']
