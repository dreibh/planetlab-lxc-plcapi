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
	return NodeGroups(self.api, nodegroup_id_or_name_list).values()
