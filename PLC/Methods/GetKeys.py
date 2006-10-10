from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Keys import Key, Keys
from PLC.Auth import PasswordAuth

class GetKeys(Method):
    """
    Get an array of structs containing the keys for the specified
    key_ids. If key_id_list is not specified, all keys
    will be queried.

    Admin may get all keys. Non-admins can only get their own keys
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        [Key.fields['key_id']]
        ]

    returns = [Key.fields]

    def call(self, auth, key_id_list = None):
        	
	#if we are not admin, make sure to only return our own keys       
        if 'admin' not in self.caller['roles']:
		if key_id_list is None:
			key_id_list =  self.caller['key_ids']
		else:
			valid_keys = lambda x: x in self.caller['key_ids']
			key_id_list = filter(valid_keys, key_id_list)
		
	keys = Keys(self.api, key_id_list).values()
		
        return keys
