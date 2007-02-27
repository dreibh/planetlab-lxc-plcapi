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

        if node['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local node"

	# Get nodegroup info
        nodegroups = NodeGroups(self.api, [nodegroup_id_or_name])
        if not nodegroups:
            raise PLCInvalidArgument, "No such nodegroup"

        nodegroup = nodegroups[0]
	
	# add node to nodegroup
        if node['node_id'] not in nodegroup['node_ids']:
            nodegroup.add_node(node)
	
	# Logging variables
	self.event_objects = {'NodeGroup': [nodegroup['nodegroup_id']],
			      'Node': [node['node_id']]}
	self.message = 'Node %d added to node group %d' % \
		(node['node_id'], nodegroup['nodegroup_id'])
        return 1
