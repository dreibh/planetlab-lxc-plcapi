from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Sites import Site, Sites
from PLC.Auth import Auth

class AdmGetSitePersons(Method):
    """
    Deprecated. See GetSites.

    Return a list of person_ids for the site specified.

    PIs may only retrieve the person_ids of accounts at their
    site. Admins may retrieve the person_ids of accounts at any site.
    """

    status = "deprecated"

    roles = ['admin', 'pi']

    accepts = [
        Auth(),
        Mixed(Site.fields['site_id'],
              Site.fields['login_base'])
        ]

    returns = Site.fields['person_ids']

    def call(self, auth, site_id_or_login_base):
        # Authenticated function
        assert self.caller is not None

        # Get site information
	sites = Sites(self.api, [site_id_or_login_base])
	if not sites:
            raise PLCInvalidArgument, "No such site"

	site = sites[0]

	if 'admin' not in self.caller['roles']: 
            if site['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to view accounts at that site"

	return site['person_ids']
