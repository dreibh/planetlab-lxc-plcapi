from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Keys import Key, Keys
from PLC.Persons import Person, Persons
from PLC.Auth import PasswordAuth

class AddKey(Method):
    """
    Adds a new key for the specified person. If the key already exists,
        the call returns successful.

    Non-admin, they can only modify their own keys.

    Returns the new key_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    can_update = lambda (field, value): field in \
                 ['key_type', 'key','is_blacklisted', 'is_primary']
    update_fields = dict(filter(can_update, Key.fields.items()))

    accepts = [
        PasswordAuth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email']),
	update_fields
        ]

    returns = Parameter(int, 'New Key_id (> 0) if successful')

    def call(self, auth, person_id_or_email, key_fields = {}):
        if filter(lambda field: field not in self.update_fields, key_fields):
            raise PLCInvalidArgument, "Invalid field specified"

        # Get account details
        persons = Persons(self.api, [person_id_or_email]).values()
        if not persons:
            raise PLCInvalidArgument, "No such account"
        person = persons[0]

	#If we are not admin, make sure caller is adding a key to their account
        if 'admin' not in self.caller['roles']:
            if person['person_id'] not in [self.caller['person_id']]:
                raise PLCPermissionDenied, "You may only modify your own keys"

        key = Key(self.api, key_fields)
        key.sync()
	key.add_person(person)
        
        return key['key_id']
