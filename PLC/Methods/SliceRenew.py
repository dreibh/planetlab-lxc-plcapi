import time

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Slices import Slice, Slices
from PLC.Auth import Auth
from PLC.Methods.UpdateSlice import UpdateSlice

class SliceRenew(UpdateSlice):
    """
    Deprecated. See UpdateSlice.

    """

    status = "deprecated"

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        Slice.fields['name'],
        Slice.fields['expires']
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, slice_name, slice_expires):

        slice_fields = {}
        slice_fields['expires'] = slice_expires

        return UpdateSlice.call(self, auth, slice_name, slice_fields)
