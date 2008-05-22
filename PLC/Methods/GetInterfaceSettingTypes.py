#
# Thierry Parmentelat - INRIA
#
# $Revision$
#
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.InterfaceSettingTypes import InterfaceSettingType, InterfaceSettingTypes

class GetInterfaceSettingTypes(Method):
    """
    Returns an array of structs containing details about
    interface setting types.

    The usual filtering scheme applies on this method.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node']

    accepts = [
        Auth(),
        Mixed([Mixed(InterfaceSettingType.fields['interface_setting_type_id'],
                     InterfaceSettingType.fields['name'])],
              Filter(InterfaceSettingType.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [InterfaceSettingType.fields]

    def call(self, auth, interface_setting_type_filter = None, return_fields = None):
        return InterfaceSettingTypes(self.api, interface_setting_type_filter, return_fields)
