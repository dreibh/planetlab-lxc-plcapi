from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Keys import Key, Keys
from PLC.Auth import Auth

can_update = lambda (field, value): field in \
             ['key_type', 'key']

class UpdateKey(Method):
    """
    Updates the parameters of an existing key with the values in
    key_fields.

    Non-admins may only update their own keys.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    key_fields = dict(filter(can_update, Key.fields.items()))

    accepts = [
        Auth(),
        Key.fields['key_id'],
        key_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, key_id, key_fields):
        key_fields = dict(filter(can_update, key_fields.items()))

        # Get key information
        keys = Keys(self.api, [key_id])
        if not keys:
            raise PLCInvalidArgument, "No such key"
        key = keys[0]

        if key['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local key"

        if 'admin' not in self.caller['roles']:
            if key['key_id'] not in self.caller['key_ids']:
                raise PLCPermissionDenied, "Key must be associated with one of your accounts"

        key.update(key_fields)
        key.sync()

        # Logging variables
        self.event_objects = {'Key': [key['key_id']]}
        self.message = 'key %d updated: %s' % \
                (key['key_id'], ", ".join(key_fields.keys()))
        return 1
