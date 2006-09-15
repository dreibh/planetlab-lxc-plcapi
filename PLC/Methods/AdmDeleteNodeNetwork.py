from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import PasswordAuth
from PLC.Nodes import Node, Nodes
from PLC.NodeNetworks import NodeNetwork, NodeNetworks

class AdmDeleteNodeNetwork(Method):
    """
    Delete an existing Node Network. Nodenetwork_id must be associated to 
    node_id and not be associated with a different node.

    Admins may delete any node network. PIs and techs can only delete 
    nodenetworks for thier nodes.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    accepts = [
        PasswordAuth(),
        Mixed(NodeNetwork.all_fields['node_id'],
	      NodeNetwork.all_fields['hostname']),
	Mixed(NodeNetwork.all_fields['nodenetwork_id'],
	      NodeNetwork.all_fields['hostname'])
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, node_id_or_hostname, nodenetwork_id_or_hostname):
        # Get node network information
        nodenetworks = NodeNetworks(self.api, [nodenetwork_id_or_hostname]).values()
        if not nodenetworks:
            raise PLCInvalidArgument, "No such node network"
	nodenetwork = nodenetworks[0]
	
	# Get node information
	nodes = Nodes(self.api, [node_id_or_hostname]).values()
	if not nodes:
		raise PLCInvalidArgument, "No such node"
	node = nodes[0]

	# Check if node network is associated with specified node
	if not node['node_id'] ==  nodenetwork['node_id'] or nodenetwork['nodenetwork_id'] not in node['nodenetwork_ids']:
		raise PLCInvalidArgument, "node network not assoicated with this node"

	assert self.caller is not None

        # If we are not an admin, make sure that the caller is a
        # member of the site at which the node is located.
        if 'admin' not in self.caller['roles']:
        	if node['site_id'] not in self.caller['site_ids']:
			raise PLCPermissionDenied, "Not allowed to delete node network at this node"
		if 'tech' not in self.caller['roles']:
                        raise PLCPermissionDenied, "Not allowed to add node network for specified node"
        nodenetwork.delete()

        return 1
