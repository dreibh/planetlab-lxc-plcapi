from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth
from PLC.Nodes import Node, Nodes
from PLC.NodeNetworks import NodeNetwork, NodeNetworks

class DeleteNodeNetwork(Method):
    """
    Delete an existing Node Network. Nodenetwork_id must be associated to 
    node_id and not be associated with a different node.

    ins may delete any node network. PIs and techs can only delete 
    nodenetworks for thier nodes.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    accepts = [
        Auth(),
	Mixed(NodeNetwork.fields['nodenetwork_id'],
	      NodeNetwork.fields['ip'])
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, nodenetwork_id_or_ip):
        # Get node network information
        nodenetworks = NodeNetworks(self.api, [nodenetwork_id_or_ip])
        if not nodenetworks:
            raise PLCInvalidArgument, "No such node network"
	nodenetwork = nodenetworks[0]
	
	# Get node information
	nodes = Nodes(self.api, [nodenetwork['node_id']])
	if not nodes:
		raise PLCInvalidArgument, "No such node"
	node = nodes[0]

        # Authenticated functino
	assert self.caller is not None

        # If we are not an admin, make sure that the caller is a
        # member of the site at which the node is located.
        if 'admin' not in self.caller['roles']:
            if node['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to delete this node network"

        nodenetwork.delete()

        return 1
