from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.Nodes import Node, Nodes
from PLC.Auth import Auth

class DeleteNodeFromNodeGroup(Method):
    """
    Removes a node from the specified node group. 

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
	Mixed(Node.fields['node_id'],
	      Node.fields['hostname']),
        Mixed(NodeGroup.fields['nodegroup_id'],
	      NodeGroup.fields['name']),
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, node_id_or_hostname, nodegroup_id_or_name):
        # Get node info
	nodes = Nodes(self.api, [node_id_or_hostname])
	if not nodes:
		raise PLCInvalidArgument, "No such node"

	node = nodes[0]

	# Get nodegroup info
        nodegroups = NodeGroups(self.api, [nodegroup_id_or_name])
        if not nodegroups:
            raise PLCInvalidArgument, "No such nodegroup"

        nodegroup = nodegroups[0]

	# Remove node from nodegroup
        if node['node_id'] in nodegroup['node_ids']:
            nodegroup.remove_node(node)

        return 1
