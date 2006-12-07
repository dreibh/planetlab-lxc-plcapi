from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.Nodes import Node, Nodes
from PLC.Auth import Auth

class AddNodeToNodeGroup(Method):
    """
    Add a node to the specified node group. If the node is
    already a member of the nodegroup, no errors are returned.

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
	PLCCheckLocalNode (node,"AddNodeToNodeGroup")

	# Get nodegroup info
        nodegroups = NodeGroups(self.api, [nodegroup_id_or_name])
        if not nodegroups:
            raise PLCInvalidArgument, "No such nodegroup"

        nodegroup = nodegroups[0]
	
	# add node to nodegroup
        if node['node_id'] not in nodegroup['node_ids']:
            nodegroup.add_node(node)
	self.object_ids = [nodegroup['nodegroup_id']]

        return 1
