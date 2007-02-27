import socket

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.NodeNetworks import NodeNetwork, NodeNetworks, valid_ip
from PLC.Auth import Auth

class AdmQueryNode(Method):
    """
    Deprecated. Functionality can be implemented with GetNodes and
    GetNodeNetworks.
    """

    status = "deprecated"

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        Auth(),
        {'node_hostname': Node.fields['hostname'],
         'nodenetwork_ip': NodeNetwork.fields['ip'],
         'nodenetwork_mac': NodeNetwork.fields['mac'],
         'nodenetwork_method': NodeNetwork.fields['method']}
        ]

    returns = [Node.fields['node_id']]

    def call(self, auth, search_vals):
        # Get possible nodenetworks
        if 'node_hostname' in search_vals:
            nodes = Nodes(self.api, [search_vals['node_hostname']])
            if not nodes:
                return []

            # No network interface filters specified
            if 'nodenetwork_ip' not in search_vals and \
               'nodenetwork_mac' not in search_vals and \
               'nodenetwork_method' not in search_vals:
                return [nodes[0]['node_id']]

            if nodes[0]['nodenetwork_ids']:
                nodenetworks = NodeNetworks(self.api, nodes[0]['nodenetwork_ids'])
            else:
                nodenetworks = []
        else:
            nodenetworks = NodeNetworks(self.api)

        if 'nodenetwork_ip' in search_vals:
            if not valid_ip(search_vals['nodenetwork_ip']):
                raise PLCInvalidArgument, "Invalid IP address"
            nodenetworks = filter(lambda nodenetwork: \
                                  socket.inet_aton(nodenetwork['ip']) == socket.inet_aton(search_vals['nodenetwork_ip']),
                                  nodenetworks)

        if 'nodenetwork_mac' in search_vals:
            nodenetworks = filter(lambda nodenetwork: \
                                 nodenetwork['mac'].lower() == search_vals['nodenetwork_mac'].lower(),
                                 nodenetworks)

        if 'nodenetwork_method' in search_vals:
            nodenetworks = filter(lambda nodenetwork: \
                                  nodenetwork['method'].lower() == search_vals['nodenetwork_method'].lower(),
                                  nodenetworks)

        return [nodenetwork['node_id'] for nodenetwork in nodenetworks]
