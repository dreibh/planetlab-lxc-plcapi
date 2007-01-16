from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Slices import Slice, Slices
from PLC.Auth import Auth

class SliceUserDel(Method):
    """
    Deprecated. Can be implemented with DeletePersonFromSlice.

    Removes the specified users from the specified slice. If the person is
    already a member of the slice, no errors are returned. 

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi']

    accepts = [
        Auth(),
        Slice.fields['name'],
        [Person.fields['email']],
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, slice_name, user_list):
        # Get account information
        persons = Persons(self.api, user_list)
        if not persons:
            raise PLCInvalidArgument, "No such account"

        # Get slice information
        slices = Slices(self.api, [slice_id_or_name])
        if not slices:
            raise PLCInvalidArgument, "No such slice"

        slice = slices[0]
	if slice['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local slice"

        # If we are not admin, make sure the caller is a PI
        # of the site associated with the slice
	if 'admin' not in self.caller['roles']:
            if slice['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to add users to this slice"
	
	for person in persons:
	    if person['person_id'] in slice['person_ids']:
                slice.remove_person(person, False)
	
	slice.sync()
	self.object_ids = [slice['slice_id']]

        return 1
