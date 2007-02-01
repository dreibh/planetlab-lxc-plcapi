from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.AddressTypes import AddressType, AddressTypes
from PLC.Auth import Auth

class GetAddressTypes(Method):
    """
    Returns an array of structs containing details about address
    types. If address_type_filter is specified and is an array of
    address type identifiers, or a struct of address type attributes,
    only address types matching the filter will be returned. If
    return_fields is specified, only the specified details will be
    returned.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node']

    accepts = [
        Auth(),
        Mixed([Mixed(AddressType.fields['address_type_id'],
                     AddressType.fields['name'])],
              Filter(AddressType.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [AddressType.fields]


    def call(self, auth, address_type_filter = None, return_fields = None):
        return AddressTypes(self.api, address_type_filter, return_fields)
