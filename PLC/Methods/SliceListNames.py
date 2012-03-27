from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.Slices import Slice, Slices
from PLC.Methods.GetSlices import GetSlices

class SliceListNames(GetSlices):
    """
    Deprecated. Can be implemented with GetSlices.

    List the names of registered slices.

    Users may only query slices of which they are members. PIs may
    query any of the slices at their sites. Admins may query any
    slice. If a slice that cannot be queried is specified in
    slice_filter, details about that slice will not be returned.
    """

    status = "deprecated"

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        Parameter(str, "Slice prefix", nullok = True)
        ]

    returns = [Slice.fields['name']]


    def call(self, auth, prefix=None):

        slice_filter = None
        if prefix:
            slice_filter = {'name': prefix+'*'}

        slices = GetSlices.call(self, auth, slice_filter)

        if not slices:
            raise PLCInvalidArgument, "No such slice"

        slice_names = [slice['name'] for slice in slices]

        return slice_names
