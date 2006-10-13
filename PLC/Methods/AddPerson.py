from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Auth import PasswordAuth

can_update = lambda (field, value): field in \
             ['title', 'email', 'password', 'phone', 'url', 'bio']

class AddPerson(Method):
    """
    Adds a new account. Any fields specified in person_fields are
    used, otherwise defaults are used.

    Accounts are disabled by default. To enable an account, use
    SetPersonEnabled() or UpdatePerson().

    Returns the new person_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin', 'pi']

    update_fields = dict(filter(can_update, Person.fields.items()))

    accepts = [
        PasswordAuth(),
        Person.fields['first_name'],
        Person.fields['last_name'],
        update_fields
        ]

    returns = Parameter(int, 'New person_id (> 0) if successful')

    def call(self, auth, first_name, last_name, person_fields = {}):
        person_fields = dict(filter(can_update, person_fields.items()))
        person = Person(self.api, person_fields)
        person['first_name'] = first_name
        person['last_name'] = last_name
        person['enabled'] = False
        person.sync()

        return person['person_id']
