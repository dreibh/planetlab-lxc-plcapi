# $Id#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Interfaces import Interface, Interfaces
from PLC.Auth import Auth

class GetInterfaces(Method):
    """
    Returns an array of structs containing details about node network
    interfacess. If interfaces_filter is specified and is an array
    of node network identifiers, or a struct of node network
    fields and values, only node network interfaces matching the filter
    will be returned.

    If return_fields is given, only the specified details will be returned.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node', 'anonymous']

    accepts = [
        Auth(),
        Mixed([Interface.fields['interface_id']],
              Parameter (int, "interface id"),
              Filter(Interface.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [Interface.fields]
    
    def call(self, auth, interface_filter = None, return_fields = None):
        return Interfaces(self.api, interface_filter, return_fields)
