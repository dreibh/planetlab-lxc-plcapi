from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Auth import Auth
from PLC.Methods.UpdatePerson import UpdatePerson

class AdmSetPersonEnabled(UpdatePerson):
    """
    Deprecated. See UpdatePerson.
    """

    status = "deprecated"

    accepts = [
        Auth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email']),
        Person.fields['enabled']
        ]

    def call(self, auth, person_id_or_email, enabled):
        return UpdatePerson.call(self, auth, person_id_or_email, {'enabled': enabled})
