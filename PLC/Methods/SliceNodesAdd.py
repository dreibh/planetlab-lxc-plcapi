from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.Slices import Slice, Slices
from PLC.Auth import Auth
from PLC.Methods.AddSliceToNodes import AddSliceToNodes

class SliceNodesAdd(AddSliceToNodes):
    """
    Deprecated. See AddSliceToNodes.

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

        return AddSliceToNodes.call(self, auth, slice_name, nodes_list)
