from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter
from PLC.Roles import Roles
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
        roles = Roles(self.api)

        # Just the role_id: name mappings
        roles = dict(filter(lambda (role_id, name): isinstance(role_id, (int, long)), \
                            roles.items()))

        # Stringify the keys!
        keys = map(str, roles.keys())

        return dict(zip(keys, roles.values()))
