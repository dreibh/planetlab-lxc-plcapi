from types import StringTypes

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Auth import PasswordAuth
from PLC.Roles import Roles

class AdmIsPersonInRole(Method):
    """
    Returns 1 if the specified account has the specified role, 0
    otherwise. This function differs from AdmGetPersonRoles() in that
    any authorized user can call it. It is currently restricted to
    verifying PI roles.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email']),
        Roles.fields['role_id']
        ]

    returns = Parameter(int, "1 if account has role, 0 otherwise")

    status = "useless"

    def call(self, auth, person_id_or_email, role_id):
        # This is a totally fucked up function. I have no idea why it
        # exists or who calls it, but here is how it is supposed to
        # work.

        # Only allow PI roles to be checked
        roles = Roles(self.api)
        if not roles.has_key(role_id) or roles[role_id] != "pi":
            raise PLCInvalidArgument, "Only the PI role may be checked"

        # Get account information
        persons = Persons(self.api, [person_id_or_email])

        # Rather than raise an error, and indicate whether or not
        # the person is real, return 0.
        if not persons:
            return 0

        person = persons.values()[0]

        if role_id in person['role_ids']:
            return 1

        return 0
