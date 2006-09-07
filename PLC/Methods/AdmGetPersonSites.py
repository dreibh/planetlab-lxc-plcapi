from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Sites import Site, Sites
from PLC.Auth import PasswordAuth

class AdmGetPersonSites(Method):
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
        # Get account information
        persons = Persons(self.api, [person_id_or_email])
        if not persons:
            raise PLCInvalidArgument, "No such account"

        person = persons.values()[0]

        # Authenticated function
        assert self.caller is not None

        # Check if we can view this account
        if not self.caller.can_view(person):
            raise PLCPermissionDenied, "Not allowed to view specified account"

        # Filter out deleted sites
        # XXX This shouldn't be necessary once the join tables are cleaned up
        if person['site_ids']:
            sites = Sites(self.api, person['site_ids'])
            return filter(lambda site_id: site_id in sites, person['site_ids'])

        return person['site_ids']
