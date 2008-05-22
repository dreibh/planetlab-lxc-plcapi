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

class UpdateInterfaceSettingType(Method):
    """
    Updates the parameters of an existing setting type
    with the values in interface_setting_type_fields.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    interface_setting_type_fields = dict(filter(can_update, InterfaceSettingType.fields.items()))

    accepts = [
        Auth(),
        Mixed(InterfaceSettingType.fields['interface_setting_type_id'],
              InterfaceSettingType.fields['name']),
        interface_setting_type_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, interface_setting_type_id_or_name, interface_setting_type_fields):
        interface_setting_type_fields = dict(filter(can_update, interface_setting_type_fields.items()))

        interface_setting_types = InterfaceSettingTypes(self.api, [interface_setting_type_id_or_name])
        if not interface_setting_types:
            raise PLCInvalidArgument, "No such setting type"
        interface_setting_type = interface_setting_types[0]

        interface_setting_type.update(interface_setting_type_fields)
        interface_setting_type.sync()
	self.object_ids = [interface_setting_type['interface_setting_type_id']]

        return 1
