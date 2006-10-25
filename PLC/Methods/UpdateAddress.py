from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Addresses import Address, Addresses
from PLC.Auth import PasswordAuth

can_update = lambda (field, value): field in \
             ['line1', 'line2', 'line3',
              'city', 'state', 'postalcode', 'country']

class UpdateAddress(Method):
    """
    Updates the parameters of an existing address with the values in
    address_fields.

    PIs may only update addresses of their own sites.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi']

    address_fields = dict(filter(can_update, Address.fields.items()))

    accepts = [
        PasswordAuth(),
        Address.fields['address_id'],
        address_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, address_id, address_fields):
        address_fields = dict(filter(can_update, address_fields.items()))

        # Get associated address details
        addresses = Addresses(self.api, [address_id]).values()
        if not addresses:
            raise PLCInvalidArgument, "No such address"
        address = addresses[0]

        if 'admin' not in self.caller['roles']:
            if address['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Address must be associated with one of your sites"

        address.update(address_fields)
        address.sync()

        return 1
