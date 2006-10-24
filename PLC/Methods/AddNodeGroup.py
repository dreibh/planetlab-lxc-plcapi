from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.Auth import PasswordAuth

can_update = lambda (field, value): field in \
             ['name', 'description']

class AddNodeGroup(Method):
    """
    Adds a new node group. Any values specified in nodegroup_fields
    are used, otherwise defaults are used.

    Returns the new nodegroup_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin']

    nodegroup_fields = dict(filter(can_update, NodeGroup.fields.items()))

    accepts = [
        PasswordAuth(),
        nodegroup_fields
        ]

    returns = Parameter(int, 'New nodegroup_id (> 0) if successful')

    event_type = 'Add'
    object_type = 'NodeGroup'
    object_ids = []

    def call(self, auth, nodegroup_fields = {}):
        nodegroup_fields = dict(filter(can_update, nodegroup_fields.items()))
        nodegroup = NodeGroup(self.api, nodegroup_fields)
        nodegroup.sync()

	self.object_ids = [nodegroup['nodegroup_id']]

        return nodegroup['nodegroup_id']
