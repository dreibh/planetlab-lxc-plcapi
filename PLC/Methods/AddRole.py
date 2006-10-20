from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Roles import Role, Roles
from PLC.Auth import PasswordAuth

class AddRole(Method):
    """
    Adds a new role.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        PasswordAuth(),
        Role.fields['role_id'],
        Role.fields['name']
        ]

    returns = Parameter(int, '1 if successful')

    event_type = 'Add'
    object_type = 'Role'
    object_ids = []

    def call(self, auth, role_id, name):
        role = Role(self.api)
        role['role_id'] = role_id
        role['name'] = name
        role.sync(insert = True)
	self.object_ids = [role['role_id']]

        return 1
