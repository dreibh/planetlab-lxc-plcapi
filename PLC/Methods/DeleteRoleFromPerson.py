from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Auth import Auth
from PLC.Roles import Role, Roles

class DeleteRoleFromPerson(Method):
    """
    Deletes the specified role from the person.

    PIs can only revoke the tech and user roles from users and techs
    at their sites. ins can revoke any role from any user.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi']

    accepts = [
        Auth(),
        Mixed(Role.fields['role_id'],
              Role.fields['name']),
        Mixed(Person.fields['person_id'],
              Person.fields['email']),
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, role_id_or_name, person_id_or_email):
        # Get role
        roles = Roles(self.api, [role_id_or_name])
        if not roles:
            raise PLCInvalidArgument, "Invalid role '%s'" % unicode(role_id_or_name)
        role = roles[0]

        # Get account information
        persons = Persons(self.api, [person_id_or_email])
        if not persons:
            raise PLCInvalidArgument, "No such account"
        person = persons[0]

        if person['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local account"

        # Authenticated function
        assert self.caller is not None

        # Check if we can update this account
        if not self.caller.can_update(person):
            raise PLCPermissionDenied, "Not allowed to update specified account"

        # Can only revoke lesser (higher) roles from others
        if 'admin' not in self.caller['roles'] and \
           role['role_id'] <= min(self.caller['role_ids']):
            raise PLCPermissionDenied, "Not allowed to revoke that role"

        if role['role_id'] in person['role_ids']:
            person.remove_role(role)

        # Logging variables
        self.event_objects = {'Person': [person['person_id']],
                              'Role': [role['role_id']]}
        self.message = "Role %d revoked from person %d" % \
                       (role['role_id'], person['person_id'])

        return 1
