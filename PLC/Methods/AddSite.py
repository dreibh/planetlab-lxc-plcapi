from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Sites import Site, Sites
from PLC.Auth import PasswordAuth

can_update = lambda (field, value): field in \
             ['is_public', 'latitude', 'longitude', 'url']

class AddSite(Method):
    """
    Adds a new site, and creates a node group for that site. Any
    fields specified in site_fields are used, otherwise defaults are
    used.

    Returns the new site_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin']

    update_fields = dict(filter(can_update, Site.fields.items()))

    accepts = [
        PasswordAuth(),
        Site.fields['name'],
        Site.fields['abbreviated_name'],
        Site.fields['login_base'],
        update_fields
        ]

    returns = Parameter(int, 'New site_id (> 0) if successful')

    event_type = 'Add'
    object_type = 'Site'
    object_ids = []

    def call(self, auth, name, abbreviated_name, login_base, site_fields = {}):
        site_fields = dict(filter(can_update, site_fields.items()))
        site = Site(self.api, site_fields)
        site['name'] = name
        site['abbreviated_name'] = abbreviated_name
        site['login_base'] = login_base
        site.sync()
	self.object_ids = [site['site_id']]
        
	return site['site_id']
