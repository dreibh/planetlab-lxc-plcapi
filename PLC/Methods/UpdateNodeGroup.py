from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.Auth import Auth

related_fields = NodeGroup.related_fields.keys()
can_update = lambda (field, value): field in \
             ['name', 'description'] + \
	     related_fields

class UpdateNodeGroup(Method):
    """
    Updates a custom node group.
     
    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    nodegroup_fields = dict(filter(can_update, NodeGroup.fields.items() + NodeGroup.related_fields.items()))

    accepts = [
        Auth(),
        Mixed(NodeGroup.fields['nodegroup_id'],
	      NodeGroup.fields['groupname']),
        nodegroup_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, nodegroup_id_or_name, nodegroup_fields):
        nodegroup_fields = dict(filter(can_update, nodegroup_fields.items()))

	# Get nodegroup information
	nodegroups = NodeGroups(self.api, [nodegroup_id_or_name])
	if not nodegroups:
            raise PLCInvalidArgument, "No such nodegroup"
	nodegroup = nodegroups[0]

	# Make requested associations
        for field in related_fields:
            if field in nodegroup_fields:
                nodegroup.associate(auth, field, nodegroup_fields[field])
                nodegroup_fields.pop(field)
	
	nodegroup.update(nodegroup_fields)
        nodegroup.sync()
	
	# Logging variables
	self.event_objects = {'NodeGroup': [nodegroup['nodegroup_id']]}
	self.message = 'Node group %d updated: %s' % \
		(nodegroup['nodegroup_id'], ", ".join(nodegroup_fields.keys()))  
        return 1
