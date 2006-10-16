from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.NodeNetworks import NodeNetwork, NodeNetworks
from PLC.Auth import PasswordAuth
from PLC.Methods.GetNodeNetworks import GetNodeNetworks

class AdmGetAllNodeNetworks(GetNodeNetworks):
    """
    Deprecated. Functionality can be implemented with GetNodes and
    GetNodeNetworks.
    """

    status = "deprecated"

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        Mixed(Node.fields['node_id'],
              Node.fields['hostname'])
        ]

    returns = [NodeNetwork.fields]

    def call(self, auth, node_id_or_hostname):
        # Authenticated function
        assert self.caller is not None

        # Get node information
        nodes = Nodes(self.api, [node_id_or_hostname]).values()
	if not nodes:
            raise PLCInvalidArgument, "No such node"
	node = nodes[0]

	# Get node networks for this node
        if node['nodenetwork_ids']:
            nodenetworks = NodeNetworks(self.api, node['nodenetwork_ids']).values()
        else:
            nodenetworks = []

        # Cast from NodeNetwork to real dict
        nodenetworks = [dict(nodenetwork) for nodenetwork in nodenetworks]
        	
 	return nodenetworks
