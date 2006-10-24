from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NodeNetworks import NodeNetwork, NodeNetworks
from PLC.Auth import PasswordAuth

class GetNodeNetworks(Method):
    """
    Return an array of structs contain details about node network
    interfaces. If nodenetwork_id_or_ip_list is specified, only
    the specified node network interfaces will be queried.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        [Mixed(NodeNetwork.fields['nodenetwork_id'],
               NodeNetwork.fields['ip'])]
        ]

    returns = [NodeNetwork.fields]

    def call(self, auth, nodenetwork_id_or_ip_list = None):
        return NodeNetworks(self.api, nodenetwork_id_or_ip_list).values()
