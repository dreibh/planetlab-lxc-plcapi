from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Keys import Key, Keys
from PLC.Auth import Auth

class AdmDeletePersonKeys(Method):
    """
    Deprecated. Functionality can be implemented with GetPersons and
    DeleteKey.

    Deletes the specified keys. Non-admins may only delete their own
    keys.

    Returns 1 if successful, faults otherwise.
    """

    status = "deprecated"

    roles = ['admin', 'pi', 'tech', 'user']

    accepts = [
        Auth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email']),
        [Key.fields['key_id']]
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, person_id_or_email, key_ids):
        # Get account information
        persons = Persons(self.api, [person_id_or_email])
        if not persons:
            raise PLCInvalidArgument, "No such account"
        person = persons[0]

        if person['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local account"

        if 'admin' not in self.caller['roles']:
            if self.caller['person_id'] != person['person_id']:
                raise PLCPermissionDenied, "Not allowed to update specified account"

        key_ids = set(key_ids).intersection(person['key_ids'])
        if not key_ids:
            return 1

        # Get associated key details
        keys = Keys(self.api, key_ids)

        for key in keys:
            key.delete()

        return 1
