from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth
from PLC.Nodes import Node, Nodes
from PLC.NodeNetworks import NodeNetwork, NodeNetworks

class DeleteNodeNetwork(Method):
    """
    Deletes an existing node network interface.

    Admins may delete any node network. PIs and techs may only delete
    node network interfaces associated with nodes at their sites.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    accepts = [
        Auth(),
	NodeNetwork.fields['nodenetwork_id']
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, nodenetwork_id):

        # Get node network information
        nodenetworks = NodeNetworks(self.api, [nodenetwork_id])
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
	self.object_ids = [nodenetwork['nodenetwork_id']]

        return 1
