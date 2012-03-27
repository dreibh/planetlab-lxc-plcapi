import time

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Slices import Slice, Slices
from PLC.Auth import Auth
from PLC.Methods.UpdateSlice import UpdateSlice

class SliceUpdate(UpdateSlice):
    """
    Deprecated. See UpdateSlice.

    """

    status = 'deprecated'

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        Slice.fields['name'],
        Slice.fields['url'],
        Slice.fields['description'],
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, slice_name, url, description):

        slice_fields = {}
        slice_fields['url'] = url
        slice_fields['description'] = description

        return UpdateSlice.call(self, auth, slice_name, slice_fields)

        return 1
