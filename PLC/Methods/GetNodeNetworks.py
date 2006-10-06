from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NodeNetworks import NodeNetwork, NodeNetworks
from PLC.Nodes import Node, Nodes
from PLC.Auth import PasswordAuth

class GetNodeNetworks(Method):
    """
    Returns all the networks this node is connected to, as an array of
    structs.
    """

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

	# Filter out undesired or None fields (XML-RPC cannot marshal
        # None) and turn each node into a real dict.
        valid_return_fields_only = lambda (key, value): value is not None
        nodenetworks = [dict(filter(valid_return_fields_only, nodenetwork.items())) \
                        for nodenetwork in nodenetworks]
       	
	return nodenetworks
