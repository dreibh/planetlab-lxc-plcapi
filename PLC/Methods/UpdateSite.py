from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Sites import Site, Sites
from PLC.Auth import Auth

related_fields = Site.related_fields.keys()
can_update = lambda (field, value): field in \
             ['name', 'abbreviated_name', 'login_base',
              'is_public', 'latitude', 'longitude', 'url',
              'max_slices', 'max_slivers', 'enabled', 'ext_consortium_id'] + \
              related_fields

class UpdateSite(Method):
    """
    Updates a site. Only the fields specified in update_fields are
    updated, all other fields are left untouched.

    PIs can only update sites they are a member of. Only admins can
    update max_slices, max_slivers, and login_base.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi']

    site_fields = dict(filter(can_update, Site.fields.items() + Site.related_fields.items()))

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

        if site['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local site"

        # Authenticated function
        assert self.caller is not None

        # If we are not an admin, make sure that the caller is a
        # member of the site.
        if 'admin' not in self.caller['roles']:
            if site['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to modify specified site"

            # Remove admin only fields
            for key in 'max_slices', 'max_slivers', 'login_base':
                if key in site_fields:
                    del site_fields[key]

        # Make requested associations
        for field in related_fields:
            if field in site_fields:
                site.associate(auth, field, site_fields[field])
                site_fields.pop(field)

        site.update(site_fields)
        site.update_last_updated(False)
        site.sync()

        # Logging variables
        self.event_objects = {'Site': [site['site_id']]}
        self.message = 'Site %d updated: %s' % \
                (site['site_id'], ", ".join(site_fields.keys()))

        return 1
