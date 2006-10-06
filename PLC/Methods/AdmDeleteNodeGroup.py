from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import PasswordAuth
from PLC.NodeGroups import NodeGroup, NodeGroups

class AdmDeleteNodeGroup(Method):
    """
    Delete an existing Node Group.

    Admins may delete any node group

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        PasswordAuth(),
        Mixed(NodeGroup.fields['nodegroup_id'],
	      NodeGroup.fields['name'])
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, node_group_id_or_name):
        # Get account information
        nodegroups = NodeGroups(self.api, [node_group_id_or_name])
        if not nodegroups:
            raise PLCInvalidArgument, "No such node group"

        nodegroup = nodegroups.values()[0]

        nodegroup.delete()

        return 1
