from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.KeyTypes import KeyType, KeyTypes
from PLC.Auth import Auth

class AddKeyType(Method):
    """
    Adds a new key type.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        KeyType.fields['key_type']
        ]

    returns = Parameter(int, '1 if successful')

    event_type = 'Add'
    object_type = 'KeyType'

    def call(self, auth, name):
        key_type = KeyType(self.api)
        key_type['key_type'] = name
        key_type.sync()

        return 1
