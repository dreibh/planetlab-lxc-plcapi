from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Keys import Key, Keys
from PLC.Persons import Person, Persons
from PLC.Auth import PasswordAuth

class AddPersonKey(Method):
    """
    Adds a new key to the specified account.

    Non-admins can only modify their own keys.

    Returns the new key_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    accepts = [
        PasswordAuth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email']),
        Key.fields['key_type'],
        Key.fields['key']
        ]

    returns = Parameter(int, 'New key_id (> 0) if successful')

    event_type = 'Add'
    object_type = 'Key'
    object_ids = []

    def call(self, auth, person_id_or_email, key_type, key_value):
        # Get account details
        persons = Persons(self.api, [person_id_or_email]).values()
        if not persons:
            raise PLCInvalidArgument, "No such account"
        person = persons[0]

	# If we are not admin, make sure caller is adding a key to their account
        if 'admin' not in self.caller['roles']:
            if person['person_id'] != self.caller['person_id']:
                raise PLCPermissionDenied, "You may only modify your own keys"

        key = Key(self.api)
        key['person_id'] = person['person_id']
        key['key_type'] = key_type
        key['key'] = key_value
        key.sync(commit = False)
        person.add_key(key, commit = True)
        self.object_ids = [key['key_id']]

        return key['key_id']
