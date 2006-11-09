from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth, BootAuth
from PLC.Nodes import Node, Nodes
from PLC.NodeNetworks import NodeNetwork, NodeNetworks

can_update = lambda (field, value): field in \
             ['method', 'mac', 'gateway', 'network',
              'broadcast', 'netmask', 'dns1', 'dns2']

class BootUpdateNode(Method):
    """
    Allows the calling node to update its own record. Only the primary
    network can be updated, and the node IP cannot be changed.

    Returns 1 if updated successfully.
    """

    roles = ['node']

    nodenetwork_fields = dict(filter(can_update, NodeNetwork.fields.items()))

    accepts = [
        BootAuth(),
        {'boot_state': Node.fields['boot_state'],
         'primary_network': nodenetwork_fields,
         'ssh_host_key': Node.fields['ssh_rsa_key']}
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, node_fields):
        # Update node state
        if node_fields.has_key('boot_state'):
            self.caller['boot_state'] = node_fields['boot_state']
        if node_fields.has_key('ssh_host_key'):
            self.caller['ssh_rsa_key'] = node_fields['ssh_host_key']

        # Update primary node network state
        if node_fields.has_key('primary_network'):
            primary_network = node_fields['primary_network'] 

            if 'nodenetwork_id' not in primary_network:
                raise PLCInvalidArgument, "Node network not specified"
            if primary_network['nodenetwork_id'] not in self.caller['nodenetwork_ids']:
                raise PLCInvalidArgument, "Node network not associated with calling node"

            nodenetworks = NodeNetworks(self.api, [primary_network['nodenetwork_id']])
            if not nodenetworks:
                raise PLCInvalidArgument, "No such node network"
            nodenetwork = nodenetworks[0]

            if not nodenetwork['is_primary']:
                raise PLCInvalidArgument, "Not the primary node network on record"

            nodenetwork_fields = dict(filter(can_update, primary_network.items()))
            nodenetwork.update(nodenetwork_fields)
            nodenetwork.sync(commit = False)

        self.caller.sync(commit = True)

        return 1
