from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.Auth import Auth

can_update = lambda (field, value): field in NodeGroup.fields.keys() and field != NodeGroup.primary_field

class AddNodeGroup(Method):
    """
    Adds a new node group. Any values specified in nodegroup_fields
    are used, otherwise defaults are used.

    Returns the new nodegroup_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin']

    nodegroup_fields = dict(filter(can_update, NodeGroup.fields.items()))

    accepts = [
        Auth(),
        nodegroup_fields
        ]

    returns = Parameter(int, 'New nodegroup_id (> 0) if successful')


    def call(self, auth, nodegroup_fields):
        nodegroup_fields = dict([f for f in nodegroup_fields.items() if can_update(f)])
        nodegroup = NodeGroup(self.api, nodegroup_fields)
        nodegroup.sync()

	# Logging variables
	self.event_objects = {'NodeGroup': [nodegroup['nodegroup_id']]}
	self.message = 'Node group %d created' % nodegroup['nodegroup_id']
 
        return nodegroup['nodegroup_id']
