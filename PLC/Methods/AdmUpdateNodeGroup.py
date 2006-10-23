from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.Auth import PasswordAuth
from PLC.Methods.UpdateNodeGroup import UpdateNodeGroup

class AdmUpdateNodeGroup(UpdateNodeGroup):
    """
    Deprecated. See UpdateNodeGroup.
    """

    status = "deprecated"

    accepts = [
        PasswordAuth(),
        Mixed(NodeGroup.fields['nodegroup_id'],
	      NodeGroup.fields['name']),
        NodeGroup.fields['name'],
     	NodeGroup.fields['description']
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, nodegroup_id_or_name, name, description):
        return UpdateNodeGroup.call(self, auth, nodegroup_id_or_name,
                                    {'name': name, 'description': description})
