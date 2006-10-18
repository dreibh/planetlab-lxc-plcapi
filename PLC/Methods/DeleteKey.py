from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Keys import Key, Keys
from PLC.Auth import PasswordAuth

class DeleteKey(Method):
    """
    Deletes a key.

    Non-admins may only delete their own keys.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    accepts = [
        PasswordAuth(),
        Key.fields['key_id'],
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, key_id):
        # Get associated key details
        keys = Keys(self.api, [key_id]).values()
        if not keys:
            raise PLCInvalidArgument, "No such key"
        key = keys[0]

        if 'admin' not in self.caller['roles']:
            if key['key_id'] not in self.caller['key_ids']:
                raise PLCPermissionDenied, "Key must be associated with your account"

        key.delete()

        return 1
