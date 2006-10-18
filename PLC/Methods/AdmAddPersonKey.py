from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Keys import Key, Keys
from PLC.Persons import Person, Persons
from PLC.Auth import PasswordAuth

class AdmAddPersonKey(AddPersonKey):
    """
    Deprecated. See AddPersonKey. Keys can no longer be marked as
    primary, i.e. the is_primary argument does nothing.
    """

    status = "deprecated"

    accepts = [
        PasswordAuth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email']),
        Key.fields['key_type'],
        Key.fields['key'],
        Parameter(int, "Make this key the primary key")
        ]

    def call(self, auth, person_id_or_email, key_type, key_value, is_primary):
        return AddPersonKey.call(self, auth, person_id_or_email, key_type, key_value)
