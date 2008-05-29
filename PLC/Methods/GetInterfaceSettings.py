#
# Thierry Parmentelat - INRIA
#
# $Revision$
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth

from PLC.InterfaceSettings import InterfaceSetting, InterfaceSettings
from PLC.Sites import Site, Sites
from PLC.Interfaces import Interface, Interfaces

class GetInterfaceSettings(Method):
    """
    Returns an array of structs containing details about
    interfaces and related settings.

    If interface_setting_filter is specified and is an array of
    interface setting identifiers, only interface settings matching
    the filter will be returned. If return_fields is specified, only
    the specified details will be returned.
    """

    roles = ['admin', 'pi', 'user', 'node']

    accepts = [
        Auth(),
        Mixed([InterfaceSetting.fields['interface_setting_id']],
              Parameter(int,"Interface setting id"),
              Filter(InterfaceSetting.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [InterfaceSetting.fields]
    

    def call(self, auth, interface_setting_filter = None, return_fields = None):

        interface_settings = InterfaceSettings(self.api, interface_setting_filter, return_fields)

        return interface_settings