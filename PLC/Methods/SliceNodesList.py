from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.Slices import Slice, Slices
from PLC.Nodes import Node, Nodes
from PLC.Methods.GetSlices import GetSlices
from PLC.Methods.GetNodes import GetNodes

class SliceNodesList(GetSlices, GetNodes):
    """
    Deprecated. Can be implemented with GetSlices and GetNodes.

    """

    status = "deprecated"

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        Slice.fields['name']
        ]

    returns = [Node.fields['hostname']]


    def call(self, auth, slice_name):
        slices = GetSlices.call(self, auth, [slice_name])
        if not slices:
            return []

        slice = slices[0]
        nodes = GetNodes.call(self, auth, slice['node_ids'])
        if not nodes:
            return []

        node_hostnames = [node['hostname'] for node in nodes]

        return node_hostnames
