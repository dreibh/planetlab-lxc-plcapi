from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Auth import Auth

class DeletePerson(Method):
    """
    Mark an existing account as deleted.

    Users and techs can only delete themselves. PIs can only delete
    themselves and other non-PIs at their sites. ins can delete
    anyone.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        Auth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email'])
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, person_id_or_email):
        # Get account information
        persons = Persons(self.api, [person_id_or_email])
        if not persons:
            raise PLCInvalidArgument, "No such account"
        person = persons[0]

        if person['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local account"

        # Authenticated function
        assert self.caller is not None

        # Check if we can update this account
        if not self.caller.can_update(person):
            raise PLCPermissionDenied, "Not allowed to delete specified account"

        person.delete()

        # Logging variables
        self.event_objects = {'Person': [person['person_id']]}
        self.message = 'Person %d deleted' % person['person_id']

        return 1
