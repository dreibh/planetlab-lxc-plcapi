from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Auth import Auth

class AdmGetPersonRoles(Method):
    """
    Deprecated. See GetPersons.

    Return the roles that the specified person has as a struct:

    {'10': 'admin', '30': 'user', '20': 'pi', '40': 'tech'}

    Admins can get the roles for any user. PIs can only get the roles
    for members of their sites. All others may only get their own
    roles.

    Note that because of XML-RPC marshalling limitations, the keys to
    this struct are string representations of the integer role
    identifiers.
    """

    status = "deprecated"

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        Auth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email'])
        ]

    returns = dict

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

        # Stringify the keys!
        role_ids = map(str, person['role_ids'])
        roles = person['roles']

        return dict(zip(role_ids, roles))
