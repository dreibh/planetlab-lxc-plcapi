from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Auth import PasswordAuth

class AdmAddPerson(Method):
    """
    Adds a new account. Any fields specified in optional_vals are
    used, otherwise defaults are used.

    Accounts are disabled by default. To enable an account, use
    AdmSetPersonEnabled() or AdmUpdatePerson().

    Returns the new person_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin', 'pi']

    can_update = lambda (field, value): field in \
                 ['title', 'email', 'password', 'phone', 'url', 'bio']
    update_fields = dict(filter(can_update, Person.fields.items()))

    accepts = [
        PasswordAuth(),
        Person.fields['first_name'],
        Person.fields['last_name'],
        update_fields
        ]

    returns = Parameter(int, 'New person_id (> 0) if successful')

    def call(self, auth, first_name, last_name, optional_vals = {}):
        if filter(lambda field: field not in self.update_fields, optional_vals):
            raise PLCInvalidArgument, "Invalid fields specified"

        person = Person(self.api, optional_vals)
        person['first_name'] = first_name
        person['last_name'] = last_name
        person['enabled'] = False
        person.flush()

        return person['person_id']
