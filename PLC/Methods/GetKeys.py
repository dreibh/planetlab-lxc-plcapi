from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Keys import Key, Keys
from PLC.Auth import PasswordAuth

class GetKeys(Method):
    """
    Return an array of structs containing details about keys. If
    key_id_list is specified, only the specified keys will be queried.

    Admin may query all keys. Non-admins may only query their own
    keys.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        [Key.fields['key_id']]
        ]

    returns = [Key.fields]

    def call(self, auth, key_ids = None):
	# If we are not admin, make sure to only return our own keys       
        if 'admin' not in self.caller['roles']:
            key_ids = set(key_ids).intersection(self.caller['key_ids'])
            if not key_ids:
                return []

	keys = Keys(self.api, key_ids).values()
	
	# Turn each key into a real dict
	keys = [dict(key) for key in keys]
		
        return keys
