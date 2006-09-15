import os

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Sites import Site, Sites
from PLC.Auth import PasswordAuth

class AdmGetSitePersons(Method):
    """
    Return a list of person_ids for the site specified.

    Admins may retrieve person_ids at any site by not specifying
    site_id_or_name or by specifying an empty list. PIs may only retrieve 
    the person_ids at their site

    """

    roles = ['admin', 'pi']

    accepts = [
        PasswordAuth(),
        Site.fields['site_id']
        ]

    returns = [Site.all_fields['person_ids']]

    def call(self, auth, site_id):
        # Authenticated function
        assert self.caller is not None

        # Get site information
	sites = Sites(self.api, [site_id], ['person_ids']).values()	

	# make sure sites are found
	if not sites:
		raise PLCInvalidArgument, "No such site"
	site = sites[0]
	if 'admin' not in self.caller['roles']: 
                if site['site_id'] not in self.caller['site_ids']:
                        raise PLCPermissionDenied, "Not allowed to update node network"
                if 'pi' not in self.caller['roles']:
                        raise PLCPermissionDenied, "User account not allowed to update node network"	
	person_ids = site['person_ids']
       
	return person_ids
