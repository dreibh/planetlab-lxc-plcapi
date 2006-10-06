from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.AddressTypes import AddressType, AddressTypes
from PLC.Auth import PasswordAuth

class UpdateAddressType(Method):
    """
    Updates the parameters of an existing address type with the values
    in address_type_fields.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    can_update = lambda (field, value): field in ['name', 'description']
    update_fields = dict(filter(can_update, AddressType.fields.items()))

    accepts = [
        PasswordAuth(),
        Mixed(AddressType.fields['address_type_id'],
              AddressType.fields['name']),
        update_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, address_type_id_or_name, address_type_fields):
        if filter(lambda field: field not in self.update_fields, address_type_fields):
            raise PLCInvalidArgument, "Invalid field specified"

        address_types = AddressTypes(self.api, [address_type_id_or_name]).values()
        if not address_types:
            raise PLCInvalidArgument, "No such address type"
        address_type = address_types[0]

        address_type.update(address_type_fields)
        address_type.sync()

        return 1
