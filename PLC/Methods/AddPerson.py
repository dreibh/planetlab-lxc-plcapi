from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Auth import Auth

can_update = lambda (field, value): field in \
             ['first_name', 'last_name', 'title',
              'email', 'password', 'phone', 'url', 'bio']

class AddPerson(Method):
    """
    Adds a new account. Any fields specified in person_fields are
    used, otherwise defaults are used.

    Accounts are disabled by default. To enable an account, use
    SetPersonEnabled() or UpdatePerson().

    Returns the new person_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin', 'pi']

    person_fields = dict(filter(can_update, Person.fields.items()))

    accepts = [
        Auth(),
        person_fields
        ]

    returns = Parameter(int, 'New person_id (> 0) if successful')

    event_type = 'Add'
    object_type = 'Person'

    def call(self, auth, person_fields):
        person_fields = dict(filter(can_update, person_fields.items()))
        person = Person(self.api, person_fields)
        person.sync()

	self.object_ids = [person['person_id']]

        return person['person_id']
