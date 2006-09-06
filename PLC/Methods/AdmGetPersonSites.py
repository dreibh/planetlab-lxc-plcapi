from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Sites import Site, Sites
from PLC.Auth import PasswordAuth

from PLC.Methods.AdmGetPersons import AdmGetPersons

class AdmGetPersonSites(AdmGetPersons):
    """
    Returns the sites that the specified person is associated with as
    an array of site identifiers.

    Admins may retrieve details about anyone. Users and techs may only
    retrieve details about themselves. PIs may retrieve details about
    themselves and others at their sites.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email'])
        ]

    returns = [Site.fields['site_id']]

    def call(self, auth, person_id_or_email):
        persons = AdmGetPersons.call(self, auth, [person_id_or_email])

        # AdmGetPersons() validates person_id_or_email
        assert persons
        person = persons[0]

        # Filter out deleted sites
        sites = Sites(self.api, persons['site_ids'])

        return [site['site_id'] for site in sites]
