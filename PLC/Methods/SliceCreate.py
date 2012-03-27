from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth
from PLC.Slices import Slice, Slices
from PLC.Methods.AddSlice import AddSlice

class SliceCreate(AddSlice):
    """
    Deprecated. See AddSlice.
    """

    status = "deprecated"

    accepts = [
        Auth(),
        Slice.fields['name'],
        AddSlice.accepts[1]
        ]

    returns = Parameter(int, 'New slice_id (> 0) if successful')

    def call(self, auth, name, slice_fields = {}):
        slice_fields['name'] = name
        return AddSlice.call(self, auth, slice_fields)
