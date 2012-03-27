from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Slices import Slice, Slices
from PLC.Auth import Auth
from PLC.Methods.AddPersonToSlice import AddPersonToSlice

class SliceUserAdd(AddPersonToSlice):
    """
    Deprecated. See AddPersonToSlice.

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
            AddPersonToSlice.call(self, auth, user, slice_name)

        return 1
