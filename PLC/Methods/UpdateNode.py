from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.Auth import PasswordAuth

can_update = lambda (field, value): field in \
             ['hostname', 'boot_state', 'model', 'version',
              'key', 'session']

class UpdateNode(Method):
    """
    Updates a node. Only the fields specified in node_fields are
    updated, all other fields are left untouched.
    
    PIs and techs can update only the nodes at their sites. Only
    admins can update the key and session fields.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    node_fields = dict(filter(can_update, Node.fields.items()))

    accepts = [
        PasswordAuth(),
        Mixed(Node.fields['node_id'],
              Node.fields['hostname']),
        node_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, node_id_or_hostname, node_fields):
        node_fields = dict(filter(can_update, node_fields.items()))

	# Remove admin only fields
	if 'admin' not in self.caller['roles']:
            for key in 'key', 'session':
                del node_fields[key]

        # Get account information
        nodes = Nodes(self.api, [node_id_or_hostname])
        if not nodes:
            raise PLCInvalidArgument, "No such node"

        node = nodes.values()[0]

        # Authenticated function
        assert self.caller is not None

        # If we are not an admin, make sure that the caller is a
        # member of the site at which the node is located.
        if 'admin' not in self.caller['roles']:
            if node['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to delete nodes from specified site"

        node.update(node_fields)
        node.sync()

        return 1
