from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.AddressTypes import AddressType, AddressTypes
from PLC.Auth import PasswordAuth

can_update = lambda (field, value): field not in ['address_type_id']

class AddAddressType(Method):
    """
    Adds a new address type. Fields specified in address_type_fields
    are used.

    Returns the new address_type_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin']

    address_type_fields = dict(filter(can_update, AddressType.fields.items()))

    accepts = [
        PasswordAuth(),
        address_type_fields
        ]

    returns = Parameter(int, 'New address_type_id (> 0) if successful')
        
    event_type = 'Add'    
    object_type = 'AddressType'
    object_ids = []

    def call(self, auth, address_type_fields = {}):
        address_type_fields = dict(filter(can_update, address_type_fields.items()))
        address_type = AddressType(self.api, address_type_fields)
        address_type.sync()

	self.object_ids = [address_type['address_type_id']]
        
	return address_type['address_type_id']
