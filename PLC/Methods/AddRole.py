from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Roles import Role, Roles
from PLC.Auth import Auth

class AddRole(Method):
    """
    Adds a new role.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Role.fields['role_id'],
        Role.fields['name']
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, role_id, name):
        role = Role(self.api)
        role['role_id'] = role_id
        role['name'] = name
        role.sync(insert = True)
        self.event_objects = {'Role': [role['role_id']]}

        return 1
