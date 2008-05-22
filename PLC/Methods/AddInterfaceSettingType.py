#
# Thierry Parmentelat - INRIA
#
# $Revision$
#


from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.InterfaceSettingTypes import InterfaceSettingType, InterfaceSettingTypes
from PLC.Auth import Auth

can_update = lambda (field, value): field in \
             ['name', 'description', 'category', 'min_role_id']

class AddInterfaceSettingType(Method):
    """
    Adds a new type of interface setting.
    Any fields specified are used, otherwise defaults are used.

    Returns the new interface_setting_id (> 0) if successful,
    faults otherwise.
    """

    roles = ['admin']

    interface_setting_type_fields = dict(filter(can_update, InterfaceSettingType.fields.items()))

    accepts = [
        Auth(),
        interface_setting_type_fields
        ]

    returns = Parameter(int, 'New interface_setting_id (> 0) if successful')


    def call(self, auth, interface_setting_type_fields):
        interface_setting_type_fields = dict(filter(can_update, interface_setting_type_fields.items()))
        interface_setting_type = InterfaceSettingType(self.api, interface_setting_type_fields)
        interface_setting_type.sync()

	self.object_ids = [interface_setting_type['interface_setting_type_id']]

        return interface_setting_type['interface_setting_type_id']
