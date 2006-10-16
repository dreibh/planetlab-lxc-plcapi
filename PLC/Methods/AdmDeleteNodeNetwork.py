from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import PasswordAuth
from PLC.Nodes import Node, Nodes
from PLC.NodeNetworks import NodeNetwork, NodeNetworks
from PLC.Methods.DeleteNodeNetwork import DeleteNodeNetwork

class AdmDeleteNodeNetwork(DeleteNodeNetwork):
    """
    Deprecated. See DeleteNodeNetwork.
    """

    accepts = [
        PasswordAuth(),
        Mixed(Node.fields['node_id'],
	      Node.fields['hostname']),
	Mixed(NodeNetwork.fields['nodenetwork_id'],
	      NodeNetwork.fields['hostname'])
        ]

    def call(self, auth, node_id_or_hostname, nodenetwork_id_or_hostname):
        return DeleteNodeNetwork.call(self, auth, nodenetwork_id_or_hostname)
