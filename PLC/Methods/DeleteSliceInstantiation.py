from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.SliceInstantiations import SliceInstantiation, SliceInstantiations
from PLC.Auth import Auth

class DeleteSliceInstantiation(Method):
    """
    Deletes a slice instantiation state.

    WARNING: This will cause the deletion of all slices of this instantiation.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        SliceInstantiation.fields['instantiation']
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, instantiation):
        slice_instantiations = SliceInstantiations(self.api, [instantiation])
        if not slice_instantiations:
            raise PLCInvalidArgument, "No such slice instantiation state"
        slice_instantiation = slice_instantiations[0]

        slice_instantiation.delete()

        return 1
