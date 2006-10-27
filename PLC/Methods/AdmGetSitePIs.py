from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Sites import Site, Sites
from PLC.Persons import Person, Persons
from PLC.Auth import Auth

class AdmGetSitePIs(Method):
    """
    Deprecated. Functionality can be implemented with GetSites and
    GetPersons.

    Return a list of person_ids of the PIs for the site specified.
    """

    status = "deprecated"

    roles = ['admin']

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
	sites = Sites(self.api, [site_id_or_login_base]).values()
	if not sites:
            raise PLCInvalidArgument, "No such site"

	site = sites[0]

        persons = Persons(self.api, site['person_ids']).values()

        has_pi_role = lambda person: 'pi' in person['roles']
        pis = filter(has_pi_role, persons)

	return [pi['person_id'] for pi in pis]
