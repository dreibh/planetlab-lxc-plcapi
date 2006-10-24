from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Auth import PasswordAuth
from PLC.Methods.AddPerson import AddPerson

can_update = lambda (field, value): field in \
             ['title', 'email', 'password', 'phone', 'url', 'bio']

class AdmAddPerson(AddPerson):
    """
    Deprecated. See AddPerson.
    """

    status = "deprecated"

    person_fields = dict(filter(can_update, Person.fields.items()))

    accepts = [
        PasswordAuth(),
        Person.fields['first_name'],
        Person.fields['last_name'],
        person_fields
        ]

    def call(self, auth, first_name, last_name, person_fields = {}):
        person_fields['first_name'] = first_name
        person_fields['last_name'] = last_name
        return AddPerson.call(self, auth, person_fields)
