from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Sites import Site, Sites
from PLC.Auth import Auth

class AdmGetPersonSites(Method):
    """
    Deprecated. See GetPersons.

    Returns the sites that the specified person is associated with as
    an array of site identifiers.

    Admins may retrieve details about anyone. Users and techs may only
    retrieve details about themselves. PIs may retrieve details about
    themselves and others at their sites.
    """

    status = "deprecated"

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        Auth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email'])
        ]

    returns = Person.fields['site_ids']

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

        return person['site_ids']
