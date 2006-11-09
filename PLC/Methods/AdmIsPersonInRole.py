from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Auth import Auth
from PLC.Roles import Role, Roles

class AdmIsPersonInRole(Method):
    """
    Deprecated. Functionality can be implemented with GetPersons.

    Returns 1 if the specified account has the specified role, 0
    otherwise. This function differs from AdmGetPersonRoles() in that
    any authorized user can call it. It is currently restricted to
    verifying PI roles.
    """

    status = "deprecated"

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        Auth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email']),
        Mixed(Parameter(int, "Role identifier"),
              Parameter(str, "Role name"))
        ]

    returns = Parameter(int, "1 if account has role, 0 otherwise")

    def call(self, auth, person_id_or_email, role_id_or_name):
        # This is a totally fucked up function. I have no idea why it
        # exists or who calls it, but here is how it is supposed to
        # work.

        # Only allow PI roles to be checked
        roles = {}
        for role in Roles(self.api):
            roles[role['role_id']] = role['name']
            roles[role['name']] = role['role_id']

        if role_id_or_name not in roles:
            raise PLCInvalidArgument, "Invalid role identifier or name"

        if isinstance(role_id_or_name, int):
            role_id = role_id_or_name
        else:
            role_id = roles[role_id_or_name]

        if roles[role_id] != "pi":
            raise PLCInvalidArgument, "Only the PI role may be checked"

        # Get account information
        persons = Persons(self.api, [person_id_or_email])

        # Rather than raise an error, and indicate whether or not
        # the person is real, return 0.
        if not persons:
            return 0

        person = persons[0]

        if role_id in person['role_ids']:
            return 1

        return 0
