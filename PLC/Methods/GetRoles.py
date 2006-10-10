from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Roles import Role, Roles
from PLC.Auth import PasswordAuth

class GetRoles(Method):
    """
    Get an array of structs containing details about all roles.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth()
        ]

    returns = [Role.fields]

    def call(self, auth):
        return Roles(self.api).values()
