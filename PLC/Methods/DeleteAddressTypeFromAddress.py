from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.AddressTypes import AddressType, AddressTypes
from PLC.Addresses import Address, Addresses
from PLC.Auth import Auth

class DeleteAddressTypeFromAddress(Method):
    """
    Deletes an address type from the specified address.

    PIs may only update addresses of their own sites.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi']

    accepts = [
        Auth(),
        Mixed(AddressType.fields['address_type_id'],
              AddressType.fields['name']),
        Address.fields['address_id']
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, address_type_id_or_name, address_id):
        address_types = AddressTypes(self.api, [address_type_id_or_name])
        if not address_types:
            raise PLCInvalidArgument, "No such address type"
        address_type = address_types[0]

        addresses = Addresses(self.api, [address_id])
        if not addresses:
            raise PLCInvalidArgument, "No such address"
        address = addresses[0]

        if 'admin' not in self.caller['roles']:
            if address['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Address must be associated with one of your sites"

        address.remove_address_type(address_type)
        self.event_objects = {'Address' : [address['address_id']],
                              'AddressType': [address_type['address_type_id']]}

        return 1
