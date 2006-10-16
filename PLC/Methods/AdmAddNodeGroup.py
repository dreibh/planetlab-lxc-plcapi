from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.Auth import PasswordAuth
from PLC.Methods.AddNodeGroup import AddNodeGroup

class AdmAddNodeGroup(AddNodeGroup):
    """
    Deprecated. See AddNodeGroup.
    """

    status = "deprecated"

    accepts = [
        PasswordAuth(),
        NodeGroup.fields['name'],
        NodeGroup.fields['description']
        ]

    def call(self, auth, name, description):
        return AddNodeGroup.call(self, auth, name, {'description': description})
