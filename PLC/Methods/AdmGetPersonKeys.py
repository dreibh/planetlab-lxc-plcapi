from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Keys import Key, Keys
from PLC.Auth import Auth
from PLC.Methods.GetKeys import GetKeys

class AdmGetPersonKeys(GetKeys):
    """
    Deprecated. Functionality can be implemented with GetPersons and
    GetKeys.
    """

    status = "deprecated"

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        Auth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email']),
        [Key.fields['key_id']]
        ]

    returns = [Key.fields]

    def call(self, auth, person_id_or_email):
        # Get account information
        persons = Persons(self.api, [person_id_or_email])
        if not persons:
            raise PLCInvalidArgument, "No such account"

        person = persons[0]

        if 'admin' not in self.caller['roles']:
            if self.caller['person_id'] != person['person_id']:
                raise PLCPermissionDenied, "Not allowed to view keys for specified account"

        return GetKeys.call(self, auth, person['key_ids'])
