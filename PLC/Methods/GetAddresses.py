from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Addresses import Address, Addresses
from PLC.Auth import Auth

class GetAddresses(Method):
    """
    Returns an array of structs containing details about addresses. If
    address_filter is specified and is an array of address
    identifiers, or a struct of address attributes, only addresses
    matching the filter will be returned. If return_fields is
    specified, only the specified details will be returned.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node']

    accepts = [
        Auth(),
        Mixed([Address.fields['address_id']],
              Filter(Address.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [Address.fields]


    def call(self, auth, address_filter = None, return_fields = None):
        return Addresses(self.api, address_filter, return_fields)
