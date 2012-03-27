from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Slices import Slice, Slices
from PLC.Auth import Auth

class AddPersonToSlice(Method):
    """
    Adds the specified person to the specified slice. If the person is
    already a member of the slice, no errors are returned.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi']

    accepts = [
        Auth(),
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
        person = persons[0]

        # Get slice information
        slices = Slices(self.api, [slice_id_or_name])
        if not slices:
            raise PLCInvalidArgument, "No such slice"
        slice = slices[0]

        # N.B. Allow foreign users to be added to local slices and
        # local users to be added to foreign slices (and, of course,
        # local users to be added to local slices).
        if person['peer_id'] is not None and slice['peer_id'] is not None:
            raise PLCInvalidArgument, "Cannot add foreign users to foreign slices"

        # If we are not admin, make sure the caller is a PI
        # of the site associated with the slice
        if 'admin' not in self.caller['roles']:
            if slice['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to add users to this slice"

        if slice['slice_id'] not in person['slice_ids']:
            slice.add_person(person)

        # Logging variables
        self.event_objects = {'Person': [person['person_id']],
                              'Slice': [slice['slice_id']]}
        self.object_ids = [slice['slice_id']]

        return 1
