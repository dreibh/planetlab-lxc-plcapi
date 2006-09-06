from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Auth import PasswordAuth

class AdmUpdatePerson(Method):
    """
    Updates a person. Only the fields specified in update_fields are
    updated, all other fields are left untouched.

    To remove a value without setting a new one in its place (for
    example, to remove an address from the person), specify -1 for int
    and double fields and 'null' for string fields. first_name and
    last_name cannot be unset.
    
    Users and techs can only update themselves. PIs can only update
    themselves and other non-PIs at their sites.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    can_update = lambda (field, value): field in \
                 ['first_name', 'last_name', 'title', 'email',
                  'password', 'phone', 'url', 'bio', 'accepted_aup']
    update_fields = dict(filter(can_update, Person.fields.items()))

    accepts = [
        PasswordAuth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email']),
        update_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, person_id_or_email, update_fields):
        if filter(lambda field: field not in self.update_fields, update_fields):
            raise PLCInvalidArgument, "Invalid field specified"

        # XML-RPC cannot marshal None, so we need special values to
        # represent "unset".
        for key, value in update_fields.iteritems():
            if value == -1 or value == "null":
                if key in ['first_name', 'last_name']:
                    raise PLCInvalidArgument, "first_name and last_name cannot be unset"
                update_fields[key] = None

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

        person.update(update_fields)
        person.flush()

        return 1
