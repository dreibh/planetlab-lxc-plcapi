from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Slices import Slice, Slices
from PLC.Auth import PasswordAuth

class AddPersonToSlice(Method):
    """
    Adds the specified person to the specified slice. If the person is
    already a member of the slice, no errors are returned. 

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        PasswordAuth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email']),
        Mixed(Slice.fields['slice_id'],
              Slice.fields['name'])
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, person_id_or_email, slice_id_or_name):
        # Get account information
        persons = Persons(self.api, [person_id_or_email])
        if not persons:
            raise PLCInvalidArgument, "No such account"

        person = persons.values()[0]

        # Get slice information
        slices = Slices(self.api, [slice_id_or_name])
        if not slices:
            raise PLCInvalidArgument, "No such slice"

        slice = slices.values()[0]

        if slice['slice_id'] not in person['slice_ids']:
            slice.add_person(person)

        return 1
