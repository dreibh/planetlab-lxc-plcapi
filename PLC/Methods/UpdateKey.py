from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Keys import Key, Keys
from PLC.Auth import PasswordAuth

class UpdateKey(Method):
    """
    Updates the parameters of an existing key with the values in
    key_fields.

    Non-admins may only update their own keys.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    can_update = lambda (field, value): field in \
                 ['key_type', 'key']
    update_fields = dict(filter(can_update, Key.fields.items()))

    accepts = [
        PasswordAuth(),
        Key.fields['key_id'],
        update_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, key_id, key_fields):
	# Make sure only valid fields are specified
	if filter(lambda field: field not in self.update_fields, key_fields):
            raise PLCInvalidArgument, "Invalid field specified"

        # Get key information
        keys = Keys(self.api, [key_id]).values()
        if not keys:
            raise PLCInvalidArgument, "No such key"
        key = keys[0]

        if 'admin' not in self.caller['roles']:
            if key['key_id'] not in self.caller['key_ids']:
                raise PLCPermissionDenied, "Key must be associated with one of your accounts"
            assert key['person_id'] == self.caller['person_id']

        key.update(key_fields)
        key.sync()

        return 1
