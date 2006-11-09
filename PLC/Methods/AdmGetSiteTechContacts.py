from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Sites import Site, Sites
from PLC.Persons import Person, Persons
from PLC.Auth import Auth

class AdmGetSiteTechContacts(Method):
    """
    Deprecated. Functionality can be implemented with GetSites and
    GetPersons.

    Return a list of person_ids of the technical contacts for the site
    specified.
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
	sites = Sites(self.api, [site_id_or_login_base])
	if not sites:
            raise PLCInvalidArgument, "No such site"

	site = sites[0]

        persons = Persons(self.api, site['person_ids'])

        has_tech_role = lambda person: 'tech' in person['roles']
        techs = filter(has_tech_role, persons)

	return [tech['person_id'] for tech in techs]
