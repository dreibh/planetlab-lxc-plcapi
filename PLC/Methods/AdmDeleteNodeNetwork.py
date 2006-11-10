from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth
from PLC.Nodes import Node, Nodes
from PLC.NodeNetworks import NodeNetwork, NodeNetworks
from PLC.Methods.DeleteNodeNetwork import DeleteNodeNetwork

class AdmDeleteNodeNetwork(DeleteNodeNetwork):
    """
    Deprecated. See DeleteNodeNetwork.
    """

    status = "deprecated"

    accepts = [
        Auth(),
        Mixed(Node.fields['node_id'],
	      Node.fields['hostname']),
	NodeNetwork.fields['nodenetwork_id']
        ]

    def call(self, auth, node_id_or_hostname, nodenetwork_id):
        return DeleteNodeNetwork.call(self, auth, nodenetwork_id)
