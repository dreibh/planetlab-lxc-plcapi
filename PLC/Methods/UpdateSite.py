from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Sites import Site, Sites
from PLC.Auth import PasswordAuth

class UpdateSite(Method):
    """
    Updates a site. Only the fields specified in update_fields are
    updated, all other fields are left untouched.

    To remove a value without setting a new one in its place (for
    example, to remove an address from the node), specify -1 for int
    and double fields and 'null' for string fields. hostname and
    boot_state cannot be unset.
    
    PIs can only update sites they are a member of. Only admins can 
    update max_slices.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi']

    can_update = lambda (field, value): field in \
                 ['name', 'abbreviated_name',
                  'is_public', 'latitude', 'longitude', 'url',
                  'max_slices', 'max_slivers']
    update_fields = dict(filter(can_update, Site.fields.items()))

    accepts = [
        PasswordAuth(),
        Mixed(Site.fields['site_id'],
              Site.fields['login_base']),
        update_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, site_id_or_login_base, update_fields):
	# Check for invalid fields
        if filter(lambda field: field not in self.update_fields, update_fields):
            raise PLCInvalidArgument, "Invalid field specified"

        # XML-RPC cannot marshal None, so we need special values to
        # represent "unset".
        for key, value in update_fields.iteritems():
            if value == -1 or value == "null":
                if key not in ['latitude', 'longitude', 'url']:
                    raise PLCInvalidArgument, "%s cannot be unset" % key
                update_fields[key] = None

        # Get site information
        sites = Sites(self.api, [site_id_or_login_base])
        if not sites:
            raise PLCInvalidArgument, "No such site"

        site = sites.values()[0]

        # Authenticated function
        assert self.caller is not None

        # If we are not an admin, make sure that the caller is a
        # member of the site.
        if 'admin' not in self.caller['roles']:
            if site['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to modify specified site"

            if 'max_slices' or 'max_slivers' in update_fields:
                raise PLCInvalidArgument, "Only admins can update max_slices and max_slivers"

        site.update(update_fields)
	site.sync()
	
	return 1
