from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Addresses import Address, Addresses
from PLC.Auth import Auth

class DeleteAddress(Method):
    """
    Deletes an address.

    PIs may only delete addresses from their own sites.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi']

    accepts = [
        Auth(),
        Address.fields['address_id'],
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, address_id):
        # Get associated address details
        addresses = Addresses(self.api, address_id)
        if not addresses:
            raise PLCInvalidArgument, "No such address"
        address = addresses[0]

        if 'admin' not in self.caller['roles']:
            if address['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Address must be associated with one of your sites"

        address.delete()

        # Logging variables
        self.event_objects = {'Address': [address['address_id']]}
        self.message = 'Address %d deleted' % address['address_id']

        return 1
