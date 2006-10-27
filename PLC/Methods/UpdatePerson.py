from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Auth import Auth

can_update = lambda (field, value): field in \
             ['first_name', 'last_name', 'title', 'email',
              'password', 'phone', 'url', 'bio', 'accepted_aup',
              'enabled']

class UpdatePerson(Method):
    """
    Updates a person. Only the fields specified in person_fields are
    updated, all other fields are left untouched.
    
    Users and techs can only update themselves. PIs can only update
    themselves and other non-PIs at their sites.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    person_fields = dict(filter(can_update, Person.fields.items()))

    accepts = [
        Auth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email']),
        person_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, person_id_or_email, person_fields):
        person_fields = dict(filter(can_update, person_fields.items()))

        # Get account information
        persons = Persons(self.api, [person_id_or_email])
        if not persons:
            raise PLCInvalidArgument, "No such account"

        person = persons.values()[0]

        # Authenticated function
        assert self.caller is not None

        # Check if we can update this account
        if not self.caller.can_update(person):
            raise PLCPermissionDenied, "Not allowed to update specified account"

        person.update(person_fields)
        person.sync()

        return 1
