from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Addresses import Address, Addresses
from PLC.Auth import PasswordAuth

class DeleteAddress(Method):
    """
    Deletes an address.

    PIs may only delete addresses from their own sites.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi']

    accepts = [
        PasswordAuth(),
        Address.fields['address_id'],
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, address_id):
        # Get associated address details
        addresses = Addresses(self.api, [address_id]).values()
        if not addresses:
            raise PLCInvalidArgument, "No such address"
        address = addresses[0]

        if 'admin' not in self.caller['roles']:
            if address['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Address must be associated with one of your sites"

        address.delete()

        return 1
