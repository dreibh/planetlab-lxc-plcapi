from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Auth import PasswordAuth
from PLC.Roles import Role, Roles

class AddRoleToPerson(Method):
    """
    Grants the specified role to the person.
    
    PIs can only grant the tech and user roles to users and techs at
    their sites. Admins can grant any role to any user.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi']

    accepts = [
        PasswordAuth(),
        Mixed(Role.fields['role_id'],
              Role.fields['name']),
        Mixed(Person.fields['person_id'],
              Person.fields['email']),
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, role_id_or_name, person_id_or_email):
        # Get all roles
        roles = {}
        for role_id, role in Roles(self.api).iteritems():
            roles[role_id] = role['name']
            roles[role['name']] = role_id

        if role_id_or_name not in roles:
            raise PLCInvalidArgument, "Invalid role identifier or name"

        if isinstance(role_id_or_name, int):
            role_id = role_id_or_name
        else:
            role_id = roles[role_id_or_name]

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

        # Can only grant lesser (higher) roles to others
        if 'admin' not in self.caller['roles'] and \
           role_id <= min(self.caller['role_ids']):
            raise PLCInvalidArgument, "Not allowed to grant that role"

        if role_id not in person['role_ids']:
            person.add_role(role_id)

        return 1
