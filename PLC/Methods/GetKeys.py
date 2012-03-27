from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Persons import Person, Persons
from PLC.Keys import Key, Keys
from PLC.Auth import Auth

class GetKeys(Method):
    """
    Returns an array of structs containing details about keys. If
    key_filter is specified and is an array of key identifiers, or a
    struct of key attributes, only keys matching the filter will be
    returned. If return_fields is specified, only the specified
    details will be returned.

    Admin may query all keys. Non-admins may only query their own
    keys.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node']

    accepts = [
        Auth(),
        Mixed([Mixed(Key.fields['key_id'])],
              Filter(Key.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [Key.fields]


    def call(self, auth, key_filter = None, return_fields = None):
        keys = Keys(self.api, key_filter, return_fields)

        # If we are not admin, make sure to only return our own keys
        if isinstance(self.caller, Person) and \
           'admin' not in self.caller['roles']:
            keys = filter(lambda key: key['key_id'] in self.caller['key_ids'], keys)

        return keys
