from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NodeTypes import NodeType, NodeTypes
from PLC.Auth import Auth

class AddNodeType(Method):
    """
    Adds a new node node type.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        NodeType.fields['node_type']
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, name):
        node_type = NodeType(self.api)
        node_type['node_type'] = name
        node_type.sync(insert = True)

        return 1
