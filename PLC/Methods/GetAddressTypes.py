from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.AddressTypes import AddressType, AddressTypes
from PLC.Auth import PasswordAuth

class GetAddressTypes(Method):
    """
    Get an array of structs containing details about valid address
    types. If address_type_id_or_name_list is specified, only the
    specified address types will be queried.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        [Mixed(AddressType.fields['address_type_id'],
               AddressType.fields['name'])]
        ]

    returns = [AddressType.fields]

    def call(self, auth, address_type_id_or_name_list = None):
        address_types = AddressTypes(self.api, address_type_id_or_name_list).values()

        return address_types
