
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.NodeGroups import NodeGroup, NodeGroups
#from PLC.Sites import Site, Sites
from PLC.Auth import PasswordAuth

class AdmAddNodeGroup(Method):
    """
    Adds a new node group. Any values specified in optional_vals are used,
    otherwise defaults are used.

    Returns the new nodegroup_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin']

    can_update = lambda (field, value): field in \
                 ['name', 'description', 'is_custom']
    update_fields = dict(filter(can_update, NodeGroup.fields.items()))
	
    accepts = [
        PasswordAuth(),
        NodeGroup.fields['name'],
        NodeGroup.fields['description'],
        update_fields
        ]

    returns = Parameter(int, 'New nodegroup_id (> 0) if successful')

    def call(self, auth, name, description, optional_vals = {}):
        if filter(lambda field: field not in self.update_fields, optional_vals):
            raise PLCInvalidArgument, "Invalid fields specified"

	# Create node group
        node_group = NodeGroup(self.api, optional_vals)
        node_group['name'] = name
        node_group['description'] = description
        node_group.flush()

        return node_group['nodegroup_id']
