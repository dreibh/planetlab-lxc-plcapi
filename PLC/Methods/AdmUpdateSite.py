from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Sites import Site, Sites
from PLC.Auth import PasswordAuth

class AdmUpdateSite(Method):
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

    roles = ['admin', 'pi', 'tech']

    cant_update = lambda (field, value): field not in \
                 ['site_id', 'nodegroup_id', 'organization_id', 'ext_consortium_id', 'date_created']
    update_fields = dict(filter(cant_update, Site.all_fields.items()))

    accepts = [
        PasswordAuth(),
        Mixed(Site.fields['site_id'],
              Site.fields['abbreviated_name']),
        update_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, site_id_or_abbrev_name, update_fields):
	# Only admin can update max_slices
	#if 'admin' not in self.caller['roles']:
	#	if update_fields.has_key('max_slices '):
	#		raise PLCInvalidArgument, "Only admins can update max_slices"
	
	# Check for invalid fields
        if filter(lambda field: field not in self.update_fields, update_fields):
            raise PLCInvalidArgument, "Invalid field specified"

        # XML-RPC cannot marshal None, so we need special values to
        # represent "unset".
        for key, value in update_fields.iteritems():
            if value == -1 or value == "null":
                if key in ['name', 'abbreviated_name', 'login_base', 'is_public', 'max_slices']:
                    raise PLCInvalidArgument, "%s cannot be unset" % key
                update_fields[key] = None

        # Get site information
        sites = Sites(self.api, [site_id_or_abbrev_name], Site.all_fields)
        if not sites :
            raise PLCInvalidArgument, "No such site"

        site = sites.values()[0]

        # If we are not an admin, make sure that the caller is a
        # member of the site at which the node is located.
        if 'admin' not in self.caller['roles']:
            	if site['site_id'] not in self.caller['site_ids']:
                	raise PLCPermissionDenied, "Not allowed to modify specified site"
		if 'tech' not in self.caller['roles']:
                        raise PLCPermissionDenied, "Not allowed to add node network for specified node"
		
	
        site.update(update_fields)
	site.flush()
	
	return 1
    
