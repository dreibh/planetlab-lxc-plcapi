from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NodeTypes import NodeType, NodeTypes
from PLC.Auth import Auth

class DeleteNodeType(Method):
    """
    Deletes a node node type.

    WARNING: This will cause the deletion of all nodes in this boot
    state.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        NodeType.fields['node_type']
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, name):
        node_types = NodeTypes(self.api, [name])
        if not node_types:
            raise PLCInvalidArgument, "No such node type"
        node_type = node_types[0]

        node_type.delete()

        return 1
