from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth
from PLC.Persons import Person, Persons
from PLC.Slices import Slice, Slices
from PLC.Methods.DeletePersonFromSlice import DeletePersonFromSlice

class SliceUserDel(Method):
    """
    Deprecated. Can be implemented with DeletePersonFromSlice.

    Removes the specified users from the specified slice. If the person is
    already a member of the slice, no errors are returned.

    Returns 1 if successful, faults otherwise.
    """

    status = "deprecated"

    roles = ['admin', 'pi']

    accepts = [
        Auth(),
        Slice.fields['name'],
        [Person.fields['email']],
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, slice_name, user_list):
        for user in user_list:
            DeletePersonFromSlice.call(self, auth, user, slice_name)

        return 1
