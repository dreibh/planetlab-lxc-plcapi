from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Keys import Key, Keys
from PLC.Auth import Auth

class DeleteKey(Method):
    """
    Deletes a key.

    Non-admins may only delete their own keys.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    accepts = [
        Auth(),
        Key.fields['key_id'],
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, key_id):
        # Get associated key details
        keys = Keys(self.api, [key_id])
        if not keys:
            raise PLCInvalidArgument, "No such key"
        key = keys[0]

        if key['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local key"

        if 'admin' not in self.caller['roles']:
            if key['key_id'] not in self.caller['key_ids']:
                raise PLCPermissionDenied, "Key must be associated with your account"

        key.delete()

        # Logging variables
        self.event_objects = {'Key': [key['key_id']]}
        self.message = 'Key %d deleted' % key['key_id']

        return 1
