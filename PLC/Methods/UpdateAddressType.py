from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.AddressTypes import AddressType, AddressTypes
from PLC.Auth import Auth

can_update = lambda (field, value): field in ['name', 'description']

class UpdateAddressType(Method):
    """
    Updates the parameters of an existing address type with the values
    in address_type_fields.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    address_type_fields = dict(filter(can_update, AddressType.fields.items()))

    accepts = [
        Auth(),
        Mixed(AddressType.fields['address_type_id'],
              AddressType.fields['name']),
        address_type_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, address_type_id_or_name, address_type_fields):
        address_type_fields = dict(filter(can_update, address_type_fields.items()))

        address_types = AddressTypes(self.api, [address_type_id_or_name])
        if not address_types:
            raise PLCInvalidArgument, "No such address type"
        address_type = address_types[0]

        address_type.update(address_type_fields)
        address_type.sync()
        self.event_objects = {'AddressType': [address_type['address_type_id']]}

        return 1
