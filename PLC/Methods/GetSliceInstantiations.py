from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.SliceInstantiations import SliceInstantiation, SliceInstantiations
from PLC.Auth import Auth

class GetSliceInstantiations(Method):
    """
    Returns an array of all valid slice instantiation states.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node']

    accepts = [
        Auth()
        ]

    returns = [SliceInstantiation.fields['instantiation']]

    def call(self, auth):
        return [slice_instantiation['instantiation'] for slice_instantiation in SliceInstantiations(self.api)]
