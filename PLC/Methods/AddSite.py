from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Sites import Site, Sites
from PLC.Auth import Auth

from PLC.Methods.AddSiteTag import AddSiteTag

can_update = lambda field_value: field_value[0] in \
             ['name', 'abbreviated_name', 'login_base',
              'is_public', 'latitude', 'longitude', 'url',
              'max_slices', 'max_slivers', 'enabled', 'ext_consortium_id']

class AddSite(Method):
    """
    Adds a new site, and creates a node group for that site. Any
    fields specified in site_fields are used, otherwise defaults are
    used.

    Returns the new site_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin']

    site_fields = dict(list(filter(can_update, list(Site.fields.items()))))

    accepts = [
        Auth(),
        site_fields
        ]

    returns = Parameter(int, 'New site_id (> 0) if successful')

    def call(self, auth, site_fields):
        site_fields = dict(list(filter(can_update, list(site_fields.items()))))
        site = Site(self.api, site_fields)
        site.sync()

        # Logging variables
        self.event_objects = {'Site': [site['site_id']]}
        self.message = 'Site %d created' % site['site_id']

        # Set Site HRN
        root_auth = self.api.config.PLC_HRN_ROOT
        tagname = 'hrn'
        tagvalue = '.'.join([root_auth, site['login_base']])
        AddSiteTag(self.api).__call__(auth,site['site_id'],tagname,tagvalue)


        return site['site_id']
