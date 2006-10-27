from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.Auth import Auth
from PLC.Methods.AddNodeGroup import AddNodeGroup

class AdmAddNodeGroup(AddNodeGroup):
    """
    Deprecated. See AddNodeGroup.
    """

    status = "deprecated"

    accepts = [
        Auth(),
        NodeGroup.fields['name'],
        NodeGroup.fields['description']
        ]

    def call(self, auth, name, description):
        return AddNodeGroup.call(self, auth, {'name': name, 'description': description})
