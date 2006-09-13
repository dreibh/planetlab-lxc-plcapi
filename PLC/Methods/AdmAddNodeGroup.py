# NodeGroup.validate_name() changes name to null. This causes database error


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

    Returns the new node_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin']

    can_update = lambda (field, value): field in \
                 ['model', 'version']
    update_fields = dict(filter(can_update, NodeGroup.fields.items()))

    accepts = [
        PasswordAuth(),
        NodeGroup.fields['name'],
        NodeGroup.fields['description'],
        NodeGroup.fields['is_custom'],
        update_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, name, description, optional_vals = {}):
        if filter(lambda field: field not in self.update_fields, optional_vals):
            raise PLCInvalidArgument, "Invalid fields specified"

        # Authenticated function
        assert self.caller is not None

        # make sure we are 'admin'
        if 'admin' not in self.caller['roles']:
        	raise PLCPermissionDenied, "Not allowed to add node groups"

	#creat node group
        node_group = NodeGroup(self.api, optional_vals)
        node_group['name'] = name
        node_group['description'] = description
        node_group.flush()

        return node_group['nodegroup_id']
