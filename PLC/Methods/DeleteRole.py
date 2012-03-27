from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Roles import Role, Roles
from PLC.Auth import Auth

class DeleteRole(Method):
    """
    Deletes a role.

    WARNING: This will remove the specified role from all accounts
    that possess it, and from all node and slice attributes that refer
    to it.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Mixed(Role.fields['role_id'],
              Role.fields['name'])
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, role_id_or_name):
        roles = Roles(self.api, [role_id_or_name])
        if not roles:
            raise PLCInvalidArgument, "No such role"
        role = roles[0]

        role.delete()
        self.event_objects = {'Role': [role['role_id']]}

        return 1
