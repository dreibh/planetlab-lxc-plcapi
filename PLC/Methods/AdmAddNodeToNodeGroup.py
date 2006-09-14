from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.Nodes import Node, Nodes
from PLC.Auth import PasswordAuth

class AdmAddNodeToNodeGroup(Method):
    """
    Add a node to the specified node group. If the node is
    already a member of the nodegroup, no errors are returned.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        PasswordAuth(),
        Mixed(NodeGroup.fields['nodegroup_id'],
	      NodeGroup.fields['name']),
	Mixed(Node.fields['node_id'],
	      Node.fields['hostname'])
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, nodegroup_id_or_name, node_id_or_hostname):
        # Get node info
	nodes = Nodes(self.api, [node_id_or_hostname])
	if not nodes:
		raise PLCInvalidArgument, "No such node"
	node = nodes.values()[0]

	# Get nodegroup info
        nodegroups = NodeGroups(self.api, [nodegroup_id_or_name])
        if not nodegroups:
            raise PLCInvalidArgument, "No such nodegroup"

        nodegroup = nodegroups.values()[0]

	# add node to nodegroup
        if node['node_id'] not in nodegroup['node_ids']:
            nodegroup.add_node(node)

        return 1
