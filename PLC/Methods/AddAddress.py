from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Addresses import Address, Addresses
from PLC.Auth import PasswordAuth
from PLC.Sites import Site, Sites

class AddAddress(Method):
    """
    Adds a new address to a site. Fields specified in
    address_fields are used; some are not optional.

    PIs may only add addresses to their own sites.

    Returns the new address_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin', 'pi']

    can_update = lambda (field, value): field in \
                 ['line1', 'line2', 'line3',
                  'city', 'state', 'postalcode', 'country']
    update_fields = dict(filter(can_update, Address.fields.items()))

    accepts = [
        PasswordAuth(),
        Mixed(Site.fields['site_id'],
              Site.fields['login_base']),
        update_fields
        ]

    returns = Parameter(int, 'New address_id (> 0) if successful')

    def call(self, auth, site_id_or_login_base, address_fields = {}):
        if filter(lambda field: field not in self.update_fields, address_fields):
            raise PLCInvalidArgument, "Invalid field specified"

        # Get associated site details
        sites = Sites(self.api, [site_id_or_login_base]).values()
        if not sites:
            raise PLCInvalidArgument, "No such site"
        site = sites[0]

        if 'admin' not in self.caller['roles']:
            if site['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Address must be associated with one of your sites"

        address = Address(self.api, address_fields)
        address['site_id'] = site['site_id']
        address.sync()

        return address['address_id']
