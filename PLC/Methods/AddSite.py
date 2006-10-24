from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Sites import Site, Sites
from PLC.Auth import PasswordAuth

can_update = lambda (field, value): field in \
             ['name', 'abbreviated_name', 'login_base',
              'is_public', 'latitude', 'longitude', 'url']

class AddSite(Method):
    """
    Adds a new site, and creates a node group for that site. Any
    fields specified in site_fields are used, otherwise defaults are
    used.

    Returns the new site_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin']

    site_fields = dict(filter(can_update, Site.fields.items()))

    accepts = [
        PasswordAuth(),
        site_fields
        ]

    returns = Parameter(int, 'New site_id (> 0) if successful')

    event_type = 'Add'
    object_type = 'Site'
    object_ids = []

    def call(self, auth, site_fields):
        site_fields = dict(filter(can_update, site_fields.items()))
        site = Site(self.api, site_fields)
        site.sync()

	self.object_ids = [site['site_id']]
        
	return site['site_id']
