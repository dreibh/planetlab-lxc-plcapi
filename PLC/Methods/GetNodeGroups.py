from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import PasswordAuth
from PLC.NodeGroups import NodeGroup, NodeGroups

class GetNodeGroups(Method):
    """
    Returns an array of structs containing details about all node
    groups. If nodegroup_id_or_name_list is specified, only the
    specified node groups will be queried.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        [Mixed(NodeGroup.fields['nodegroup_id'],
	       NodeGroup.fields['name'])]
        ]

    returns = [NodeGroup.fields]
  
    def call(self, auth, nodegroup_id_or_name_list = None):
        # Get node group details
	nodegroups = NodeGroups(self.api, nodegroup_id_or_name_list).values()

	# Filter out undesired or None fields (XML-RPC cannot marshal
        # None) and turn each nodegroup into a real dict.
        valid_return_fields_only = lambda (key, value): value is not None
        nodegroups = [dict(filter(valid_return_fields_only, nodegroup.items())) \
                      for nodegroup in nodegroups]

        return nodegroups
