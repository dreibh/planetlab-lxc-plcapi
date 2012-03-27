from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.AddressTypes import AddressType, AddressTypes
from PLC.Auth import Auth

class DeleteAddressType(Method):
    """
    Deletes an address type.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Mixed(AddressType.fields['address_type_id'],
              AddressType.fields['name'])
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, address_type_id_or_name):
        address_types = AddressTypes(self.api, [address_type_id_or_name])
        if not address_types:
            raise PLCInvalidArgument, "No such address type"
        address_type = address_types[0]
        address_type.delete()
        self.event_objects = {'AddressType': [address_type['address_type_id']]}

        return 1
