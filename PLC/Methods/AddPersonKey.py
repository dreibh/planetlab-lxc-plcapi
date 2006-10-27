from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Keys import Key, Keys
from PLC.Persons import Person, Persons
from PLC.Auth import Auth

can_update = lambda (field, value): field not in ['key_id']

class AddPersonKey(Method):
    """
    Adds a new key to the specified account.

    Non-admins can only modify their own keys.

    Returns the new key_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    key_fields = dict(filter(can_update, Key.fields.items()))

    accepts = [
        Auth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email']),
        key_fields
        ]

    returns = Parameter(int, 'New key_id (> 0) if successful')

    event_type = 'Add'
    object_type = 'Key'
    object_ids = []

    def call(self, auth, person_id_or_email, key_fields):
        key_fields = dict(filter(can_update, key_fields.items()))

        # Get account details
        persons = Persons(self.api, [person_id_or_email]).values()
        if not persons:
            raise PLCInvalidArgument, "No such account"
        person = persons[0]

	# If we are not admin, make sure caller is adding a key to their account
        if 'admin' not in self.caller['roles']:
            if person['person_id'] != self.caller['person_id']:
                raise PLCPermissionDenied, "You may only modify your own keys"

        key = Key(self.api, key_fields)
        key.sync(commit = False)
        person.add_key(key, commit = True)

        self.object_ids = [person['person_id'], key['key_id']]

        return key['key_id']
