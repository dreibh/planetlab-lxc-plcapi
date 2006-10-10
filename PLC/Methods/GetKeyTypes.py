from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.KeyTypes import KeyType, KeyTypes
from PLC.Auth import PasswordAuth

class GetKeyTypes(Method):
    """
    Returns a list of all valid key types.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth()
        ]

    returns = [KeyType.fields['key_type']]

    def call(self, auth):
        return [key_type['key_type'] for key_type in KeyTypes(self.api).values()]
