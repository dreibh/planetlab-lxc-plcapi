from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter
from PLC.Roles import Role, Roles
from PLC.Auth import PasswordAuth

class AdmGetAllRoles(Method):
    """
    Return all possible roles as a struct:

    {'10': 'admin', '20': 'pi', '30': 'user', '40': 'tech'}

    Note that because of XML-RPC marshalling limitations, the keys to
    this struct are string representations of the integer role
    identifiers.
    """

    roles = ['admin', 'pi', 'user', 'tech']
    accepts = [PasswordAuth()]
    returns = dict

    def call(self, auth):
        roles_list = Roles(self.api).values()

        roles_dict = {}
        for role in roles_list:
            # Stringify the keys!
            roles_dict[str(role['role_id'])] = role['name']

        return roles_dict
