# $Id$
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth, BootAuth, SessionAuth
from PLC.Nodes import Node, Nodes
from PLC.Interfaces import Interface, Interfaces

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

    interface_fields = dict(filter(can_update, Interface.fields.items()))

    accepts = [
        Mixed(BootAuth(), SessionAuth()),
        {'boot_state': Node.fields['boot_state'],
         'primary_network': interface_fields,
         'ssh_host_key': Node.fields['ssh_rsa_key']}
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, node_fields):
        # Update node state
        if node_fields.has_key('boot_state'):
            self.caller['boot_state'] = node_fields['boot_state']
        if node_fields.has_key('ssh_host_key'):
            self.caller['ssh_rsa_key'] = node_fields['ssh_host_key']

        # Update primary interface state
        if node_fields.has_key('primary_network'):
            primary_network = node_fields['primary_network'] 

            if 'interface_id' not in primary_network:
                raise PLCInvalidArgument, "Interface not specified"
            if primary_network['interface_id'] not in self.caller['interface_ids']:
                raise PLCInvalidArgument, "Interface not associated with calling node"

            interfaces = Interfaces(self.api, [primary_network['interface_id']])
            if not interfaces:
                raise PLCInvalidArgument, "No such interface %r"%interface_id
            interface = interfaces[0]

            if not interface['is_primary']:
                raise PLCInvalidArgument, "Not the primary interface on record"

            interface_fields = dict(filter(can_update, primary_network.items()))
            interface.update(interface_fields)
            interface.sync(commit = False)

        self.caller.sync(commit = True)
	self.message = "Node updated: %s" % ", ".join(node_fields.keys())

        return 1
