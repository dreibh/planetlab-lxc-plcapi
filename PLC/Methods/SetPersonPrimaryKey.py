from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Keys import Key, Keys
from PLC.Auth import PasswordAuth

class SetPersonPrimaryKey(Method):
    """
    Makes the specified key the person's primary key. The person
    must already be associated with the key.

    Admins may update anyone. All others may only update themselves.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email']),
        Key.fields['key_id']
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, person_id_or_email, key_id):
        # Get account information
        persons = Persons(self.api, [person_id_or_email])
        if not persons:
            raise PLCInvalidArgument, "No such account"

        person = persons.values()[0]

        # Authenticated function
        assert self.caller is not None

        # Get key information
        keys = Keys(self.api, [key_id])
        if not keys:
            raise PLCInvalidArgument, "No such key"

        key = keys.values()[0]

	if 'admin' not in self.caller['roles']:
        	if key['key_id'] not in person['key_ids']:
            		raise PLCInvalidArgument, "Not associated with specified key"

        key.set_primary_key(person)

        return 1
