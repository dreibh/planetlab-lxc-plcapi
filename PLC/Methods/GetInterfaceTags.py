#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth

from PLC.InterfaceTags import InterfaceTag, InterfaceTags
from PLC.Sites import Site, Sites
from PLC.Interfaces import Interface, Interfaces

class GetInterfaceTags(Method):
    """
    Returns an array of structs containing details about
    interfaces and related settings.

    If interface_tag_filter is specified and is an array of
    interface setting identifiers, only interface settings matching
    the filter will be returned. If return_fields is specified, only
    the specified details will be returned.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node']

    accepts = [
        Auth(),
        Mixed([InterfaceTag.fields['interface_tag_id']],
              Parameter(int,"Interface setting id"),
              Filter(InterfaceTag.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [InterfaceTag.fields]


    def call(self, auth, interface_tag_filter = None, return_fields = None):

        interface_tags = InterfaceTags(self.api, interface_tag_filter, return_fields)

        return interface_tags
