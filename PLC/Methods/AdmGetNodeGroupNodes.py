from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth
from PLC.NodeGroups import NodeGroup, NodeGroups

class AdmGetNodeGroupNodes(Method):
    """
    Deprecated. See GetNodeGroups.

    Returns a list of node_ids for the node group specified.
    """

    status = "deprecated"

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        Auth(),
        Mixed(NodeGroup.fields['nodegroup_id'],
	      NodeGroup.fields['name'])
        ]

    returns = NodeGroup.fields['node_ids']

    def call(self, auth, nodegroup_id_or_name):
        # Get nodes in this nodegroup
	nodegroups = NodeGroups(self.api, [nodegroup_id_or_name])
	if not nodegroups:
            raise PLCInvalidArgument, "No such node group"

	# Get the info for the node group specified
	nodegroup = nodegroups.values()[0]

	# Return the list of node_ids
        return nodegroup['node_ids']
