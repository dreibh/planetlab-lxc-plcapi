from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NodeTypes import NodeType, NodeTypes
from PLC.Auth import Auth

class GetNodeTypes(Method):
    """
    Returns an array of all valid node node types.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node']

    accepts = [
        Auth()
        ]

    returns = [NodeType.fields['node_type']]


    def call(self, auth):
        return [node_type['node_type'] for node_type in NodeTypes(self.api)]
