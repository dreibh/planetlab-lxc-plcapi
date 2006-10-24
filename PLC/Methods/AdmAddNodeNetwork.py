from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NodeNetworks import NodeNetwork, NodeNetworks
from PLC.Auth import PasswordAuth
from PLC.Methods.AddNodeNetwork import AddNodeNetwork

can_update = lambda (field, value): field not in ['nodenetwork_id', 'node_id', 'method', 'type']

class AdmAddNodeNetwork(AddNodeNetwork):
    """
    Deprecated. See AddNodeNetwork.
    """

    status = "deprecated"

    nodenetwork_fields = dict(filter(can_update, NodeNetwork.fields.items()))

    accepts = [
        PasswordAuth(),
        NodeNetwork.fields['node_id'],
        NodeNetwork.fields['method'],
        NodeNetwork.fields['type'],
        nodenetwork_fields
        ]

    def call(self, auth, node_id, method, type, nodenetwork_fields = {}):
        nodenetwork_fields['node_id'] = node_id
        nodenetwork_fields['method'] = method
        nodenetwork_fields['type'] = type
        return AddNodeNetwork.call(self, auth, nodenetwork_fields)
