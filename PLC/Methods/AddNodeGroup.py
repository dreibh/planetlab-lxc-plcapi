from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.Auth import PasswordAuth

class AddNodeGroup(Method):
    """
    Adds a new node group. Any values specified in optional_vals are used,
    otherwise defaults are used.

    Returns the new nodegroup_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        PasswordAuth(),
        NodeGroup.fields['name'],
        NodeGroup.fields['description']
        ]

    returns = Parameter(int, 'New nodegroup_id (> 0) if successful')

    def call(self, auth, name, description):
	# Create node group
        nodegroup = NodeGroup(self.api, {'name': name, 'description': description})
        nodegroup.sync()

        return nodegroup['nodegroup_id']
