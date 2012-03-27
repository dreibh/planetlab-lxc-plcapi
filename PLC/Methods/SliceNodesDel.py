from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.Slices import Slice, Slices
from PLC.Auth import Auth
from PLC.Methods.DeleteSliceFromNodes import DeleteSliceFromNodes

class SliceNodesDel(DeleteSliceFromNodes):
    """
    Deprecated. See DeleteSliceFromNodes.

    """

    status = "deprecated"

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        Slice.fields['name'],
        [Node.fields['hostname']]
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, slice_name, nodes_list):

        return DeleteSliceFromNodes.call(self, auth, slice_name, nodes_list)
