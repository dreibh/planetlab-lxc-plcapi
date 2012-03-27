from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.SliceInstantiations import SliceInstantiation, SliceInstantiations
from PLC.Auth import Auth

class AddSliceInstantiation(Method):
    """
    Adds a new slice instantiation state.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        SliceInstantiation.fields['instantiation']
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, name):
        slice_instantiation = SliceInstantiation(self.api)
        slice_instantiation['instantiation'] = name
        slice_instantiation.sync(insert = True)

        return 1
