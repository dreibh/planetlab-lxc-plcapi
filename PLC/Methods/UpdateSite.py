from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Sites import Site, Sites
from PLC.Auth import Auth

can_update = lambda (field, value): field in \
             ['name', 'abbreviated_name', 'login_base',
              'is_public', 'latitude', 'longitude', 'url',
              'max_slices', 'max_slivers']

class UpdateSite(Method):
    """
    Updates a site. Only the fields specified in update_fields are
    updated, all other fields are left untouched.

    PIs can only update sites they are a member of. Only admins can 
    update max_slices, max_slivers, and login_base.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi']

    site_fields = dict(filter(can_update, Site.fields.items()))

    accepts = [
        Auth(),
        Mixed(Site.fields['site_id'],
              Site.fields['login_base']),
        site_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, site_id_or_login_base, site_fields):
        site_fields = dict(filter(can_update, site_fields.items()))

        # Get site information
        sites = Sites(self.api, [site_id_or_login_base])
        if not sites:
            raise PLCInvalidArgument, "No such site"

        site = sites[0]
	PLCCheckLocalSite(site,"UpdateSite")

        # Authenticated function
        assert self.caller is not None

        # If we are not an admin, make sure that the caller is a
        # member of the site.
        if 'admin' not in self.caller['roles']:
            if site['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to modify specified site"

            # Remove admin only fields
            for key in 'max_slices', 'max_slivers', 'login_base':
                del site_fields[key]

        site.update(site_fields)
	site.sync()
	
	# Logging variables
	self.object_ids = [site['site_id']]
	self.message = 'Site %d updated: %s' % \
		(site['site_id'], ", ".join(site_fields.keys()))  	
	
	return 1
