from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.Auth import PasswordAuth

class AdmUpdateNodeGroup(Method):
    """
    Updates a custom node group.
     
    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        PasswordAuth(),
	NodeGroup.fields['nodegroup_id'],
        NodeGroup.fields['name'],
     	NodeGroup.fields['description']
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, nodegroup_id_or_name, name, description):
	# Get nodegroup information
	nodegroups = NodeGroups(self.api, [nodegroup_id_or_name])
	if not nodegroups:
            raise PLCInvalidArgument, "No such nodegroup"

	nodegroup = nodegroups.values()[0]
	
	# Modify node group
        update_fields = {
            'name': name,
            'description': description
            }

	nodegroup.update(update_fields)
        nodegroup.flush()

        return 1
