from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Keys import Key, Keys
from PLC.Auth import Auth

class GetKeys(Method):
    """
    Returns an array of structs containing details about keys. If
    key_ids is specified, only the specified keys will be queried.

    Admin may query all keys. Non-admins may only query their own
    keys.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        Auth(),
        [Key.fields['key_id']]
        ]

    returns = [Key.fields]

    def call(self, auth, key_ids = None):
	# If we are not admin, make sure to only return our own keys       
        if 'admin' not in self.caller['roles']:
            key_ids = set(key_ids).intersection(self.caller['key_ids'])
            if not key_ids:
                return []

	return Keys(self.api, key_ids).values()
