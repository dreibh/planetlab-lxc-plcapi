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

class DeleteInterfaceSettingType(Method):
    """
    Deletes the specified interface setting type.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Mixed(InterfaceSettingType.fields['interface_setting_type_id'],
              InterfaceSettingType.fields['name']),
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, interface_setting_type_id_or_name):
        interface_setting_types = InterfaceSettingTypes(self.api, [interface_setting_type_id_or_name])
        if not interface_setting_types:
            raise PLCInvalidArgument, "No such interface setting type"
        interface_setting_type = interface_setting_types[0]

        interface_setting_type.delete()
	self.object_ids = [interface_setting_type['interface_setting_type_id']]

        return 1
