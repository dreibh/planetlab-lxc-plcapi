from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter
from PLC.Auth import PasswordAuth
from PLC.Methods.GetRoles import GetRoles

class AdmGetAllRoles(GetRoles):
    """
    Deprecated. See GetRoles.

    Return all possible roles as a struct:

    {'10': 'admin', '20': 'pi', '30': 'user', '40': 'tech'}

    Note that because of XML-RPC marshalling limitations, the keys to
    this struct are string representations of the integer role
    identifiers.
    """

    status = "deprecated"

    returns = dict

    def call(self, auth):
        roles_list = GetRoles.call(self, auth)

        roles_dict = {}
        for role in roles_list:
            # Stringify the keys!
            roles_dict[str(role['role_id'])] = role['name']

        return roles_dict
