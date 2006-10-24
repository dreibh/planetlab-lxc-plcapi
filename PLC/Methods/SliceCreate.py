from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import PasswordAuth
from PLC.Slices import Slice, Slices
from PLC.Methods.AddSlice import AddSlice

class SliceCreate(AddSlice):
    """
    Deprecated. See AddSlice.
    """

    status = "deprecated"
    
    accepts = [
        PasswordAuth(),
        Slice.fields['name'],
        AddSlice.accepts[1]
        ]

    def call(self, auth, name, slice_fields = {}):
        slice_fields['name'] = name
        return AddSlice.call(self, auth, slice_fields)
