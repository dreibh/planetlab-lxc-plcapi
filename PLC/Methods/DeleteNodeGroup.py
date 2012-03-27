from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth
from PLC.NodeGroups import NodeGroup, NodeGroups

class DeleteNodeGroup(Method):
    """
    Delete an existing Node Group.

    ins may delete any node group

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Mixed(NodeGroup.fields['nodegroup_id'],
              NodeGroup.fields['groupname'])
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, node_group_id_or_name):
        # Get account information
        nodegroups = NodeGroups(self.api, [node_group_id_or_name])
        if not nodegroups:
            raise PLCInvalidArgument, "No such node group"

        nodegroup = nodegroups[0]

        nodegroup.delete()

        # Logging variables
        self.event_objects = {'NodeGroup': [nodegroup['nodegroup_id']]}
        self.message  = 'Node group %d deleted' % nodegroup['nodegroup_id']

        return 1
