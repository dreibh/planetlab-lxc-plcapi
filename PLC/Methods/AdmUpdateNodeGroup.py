
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.NodeGroups import NodeGroup, NodeGroups
#from PLC.Sites import Site, Sites
from PLC.Auth import PasswordAuth

class AdmUpdateNodeGroup(Method):
    """
    Updates a custom node group.
     
    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    can_update = lambda (field, value): field in \
                 ['name', 'description']
    update_fields = dict(filter(can_update, NodeGroup.fields.items()))

    accepts = [
        PasswordAuth(),
	NodeGroup.fields['nodegroup_id'],
        NodeGroup.fields['name'],
     	NodeGroup.fields['description']
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, nodegroup_id, name, description):
        #if filter(lambda field: field not in self.update_fields, optional_vals):
        #    raise PLCInvalidArgument, "Invalid fields specified"

        # Authenticated function
        assert self.caller is not None

        # make sure we are 'admin'
        if 'admin' not in self.caller['roles']:
        	raise PLCPermissionDenied, "Not allowed to update node groups"

	# Get nodegroup information
	nodegroups = NodeGroups(self.api, [nodegroup_id])
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
