from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Sites import Site, Sites
from PLC.Auth import PasswordAuth

class AdmAddSite(Method):
    """
    Adds a new site, and creates a node group for that site. Any
    fields specified in optional_vals are used, otherwise defaults are
    used.

    Returns the new site_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin']

    can_update = lambda (field, value): field in \
                 ['is_public', 'latitude', 'longitude', 'url',
                  'organization_id', 'ext_consortium_id']
    update_fields = dict(filter(can_update, Site.fields.items()))

    accepts = [
        PasswordAuth(),
        Site.fields['name'],
        Site.fields['abbreviated_name'],
        Site.fields['login_base'],
        update_fields
        ]

    returns = Parameter(int, 'New site_id (> 0) if successful')

    def call(self, auth, name, abbreviated_name, login_base, optional_vals = {}):
        if filter(lambda field: field not in self.update_fields, optional_vals):
            raise PLCInvalidArgument, "Invalid field specified"

        site = Site(self.api, optional_vals)
        site['name'] = name
        site['abbreviated_name'] = abbreviated_name
        site['login_base'] = login_base
        site.flush()

        return site['site_id']
