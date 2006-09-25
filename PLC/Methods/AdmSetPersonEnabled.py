from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Auth import PasswordAuth

class AdmSetPersonEnabled(Method):
    """
    Enables or disables a person.

    Users and techs can only update themselves. PIs can only update
    themselves and other non-PIs at their sites. Admins can update
    anyone.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi']

    accepts = [
        PasswordAuth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email']),
        Person.fields['enabled']
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, person_id_or_email, enabled):
        # Get account information
        persons = Persons(self.api, [person_id_or_email])
        if not persons:
            raise PLCInvalidArgument, "No such account"

        person = persons.values()[0]

        # Authenticated function
        assert self.caller is not None

        # Check if we can update this account
        if not self.caller.can_update(person):
            raise PLCPermissionDenied, "Not allowed to enable specified account"

        person['enabled'] = enabled
        person.sync()

        return 1
