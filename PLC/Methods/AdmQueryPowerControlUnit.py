import socket

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.PCUs import PCU, PCUs
from PLC.Nodes import Node, Nodes
from PLC.NodeNetworks import NodeNetwork, NodeNetworks, valid_ip
from PLC.Auth import PasswordAuth

class AdmQueryPowerControlUnit(Method):
    """
    Deprecated. Functionality can be implemented with GetPCUs or
    GetNodes.
    """

    status = "deprecated"

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        {'pcu_hostname': PCU.fields['hostname'],
         'pcu_ip': PCU.fields['ip'],
         'node_hostname': Node.fields['hostname'],
         'node_id': Node.fields['node_id']}
        ]

    returns = [PCU.fields['pcu_id']]

    def call(self, auth, search_vals):
        # Get all PCUs. This is a stupid function. The API should not
        # be used for DB mining.
        pcus = PCUs(self.api).values()

        if 'pcu_hostname' in search_vals:
            pcus = filter(lambda pcu: \
                          pcu['hostname'].lower() == search_vals['pcu_hostname'].lower(),
                          pcus)

        if 'pcu_ip' in search_vals:
            if not valid_ip(search_vals['pcu_ip']):
                raise PLCInvalidArgument, "Invalid IP address"
            pcus = filter(lambda pcu: \
                          socket.inet_aton(pcu['ip']) == socket.inet_aton(search_vals['pcu_ip']),
                          pcus)

        if 'node_id' in search_vals:
            pcus = filter(lambda pcu: \
                          search_vals['node_id'] in pcu['node_ids'],
                          pcus)

        if 'node_hostname' in search_vals:
            pcus = filter(lambda pcu: \
                          search_vals['node_hostname'] in \
                          [node['hostname'] for node in Nodes(self.api, pcu['node_ids']).values()],
                          pcus)

        return [pcu['pcu_id'] for pcu in pcus]
