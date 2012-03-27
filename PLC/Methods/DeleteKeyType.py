from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.KeyTypes import KeyType, KeyTypes
from PLC.Auth import Auth

class DeleteKeyType(Method):
    """
    Deletes a key type.

    WARNING: This will cause the deletion of all keys of this type.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        KeyType.fields['key_type']
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, name):
        key_types = KeyTypes(self.api, [name])
        if not key_types:
            raise PLCInvalidArgument, "No such key type"
        key_type = key_types[0]

        key_type.delete()

        return 1
