import re

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Slices import Slice, Slices
from PLC.Auth import Auth
from PLC.Methods.DeleteSlice import DeleteSlice

class SliceDelete(DeleteSlice):
    """
    Deprecated. See DeleteSlice.

    """

    status = "deprecated"

    roles = ['admin', 'pi']

    accepts = [
        Auth(),
        Slice.fields['name']
        ]

    returns = Parameter(int, 'Returns 1 if successful, a fault otherwise.')

    def call(self, auth, slice_name):

        return DeleteSlice.call(self, auth, slice_name)
