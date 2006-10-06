from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Auth import PasswordAuth
from PLC.Roles import Roles

class DeleteRoleFromPerson(Method):
    """
    Deletes the specified role from the person.
    
    PIs can only revoke the tech and user roles from users and techs
    at their sites. ins can revoke any role from any user.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi']

    accepts = [
        PasswordAuth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email']),
        Parameter(int, 'Role ID')
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, person_id_or_email, role_id):
        # Get all roles
        roles = Roles(self.api)
        if role_id not in roles:
            raise PLCInvalidArgument, "Invalid role ID"

        # Get account information
        persons = Persons(self.api, [person_id_or_email])
        if not persons:
            raise PLCInvalidArgument, "No such account"

        person = persons.values()[0]

        # Authenticated function
        assert self.caller is not None

        # Check if we can update this account
        if not self.caller.can_update(person):
            raise PLCPermissionDenied, "Not allowed to update specified account"

        # Can only revoke lesser (higher) roles from others
        if 'admin' not in self.caller['roles'] and \
           role_id <= min(self.caller['role_ids']):
            raise PLCPermissionDenied, "Not allowed to revoke that role"

        if role_id in person['role_ids']:
            person.remove_role(role_id)

        return 1
