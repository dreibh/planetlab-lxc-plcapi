from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.Auth import PasswordAuth

can_update = lambda (field, value): field in \
             ['name', 'description']

class UpdateNodeGroup(Method):
    """
    Updates a custom node group.
     
    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    update_fields = dict(filter(can_update, NodeGroup.fields.items()))

    accepts = [
        PasswordAuth(),
        Mixed(NodeGroup.fields['nodegroup_id'],
	      NodeGroup.fields['name']),
        update_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, nodegroup_id_or_name, nodegroup_fields = {}):
        nodegroup_fields = dict(filter(can_update, nodegroup_fields.items()))

	# Get nodegroup information
	nodegroups = NodeGroups(self.api, [nodegroup_id_or_name])
	if not nodegroups:
            raise PLCInvalidArgument, "No such nodegroup"
	nodegroup = nodegroups.values()[0]
	
	nodegroup.update(nodegroup_fields)
        nodegroup.sync()

        return 1
