from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.AddressTypes import AddressType, AddressTypes
from PLC.Auth import PasswordAuth

can_update = lambda (field, value): field in ['description']

class AddAddressType(Method):
    """
    Adds a new address type. Fields specified in address_type_fields
    are used.

    Returns the new address_type_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin']

    update_fields = dict(filter(can_update, AddressType.fields.items()))

    accepts = [
        PasswordAuth(),
        AddressType.fields['name'],
        update_fields
        ]

    returns = Parameter(int, 'New address_type_id (> 0) if successful')

    def call(self, auth, name, address_type_fields = {}):
        address_type_fields = dict(filter(can_update, address_type_fields.items()))
        address_type = AddressType(self.api, address_type_fields)
        address_type['name'] = name
        address_type.sync()

        return address_type['address_type_id']
