# $Id$
# $URL$
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
         ### BEWARE that the expected formerly did not match the native Node field
         # support both for now
         'ssh_rsa_key': Node.fields['ssh_rsa_key'],
         'ssh_host_key': Node.fields['ssh_rsa_key'],
         }]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, node_fields):

        if not isinstance(self.caller, Node):
            raise PLCInvalidArgument,"Caller is expected to be a node"

        node = self.caller

        # log this event only if a change occured
        # otherwise the db gets spammed with meaningless entries
        changed_fields = []
        # Update node state
        if node_fields.has_key('boot_state'):
            if node['boot_state'] != node_fields['boot_state']: changed_fields.append('boot_state')
            node['boot_state'] = node_fields['boot_state']
        ### for legacy BootManager
        if node_fields.has_key('ssh_host_key'):
            if node['ssh_rsa_key'] != node_fields['ssh_host_key']: changed_fields.append('ssh_rsa_key')
            node['ssh_rsa_key'] = node_fields['ssh_host_key']
        if node_fields.has_key('ssh_rsa_key'):
            if node['ssh_rsa_key'] != node_fields['ssh_rsa_key']: changed_fields.append('ssh_rsa_key')
            node['ssh_rsa_key'] = node_fields['ssh_rsa_key']

        # Update primary interface state
        if node_fields.has_key('primary_network'):
            primary_network = node_fields['primary_network'] 

            if 'interface_id' not in primary_network:
                raise PLCInvalidArgument, "Interface not specified"
            if primary_network['interface_id'] not in node['interface_ids']:
                raise PLCInvalidArgument, "Interface not associated with calling node"

            interfaces = Interfaces(self.api, [primary_network['interface_id']])
            if not interfaces:
                raise PLCInvalidArgument, "No such interface %r"%interface_id
            interface = interfaces[0]

            if not interface['is_primary']:
                raise PLCInvalidArgument, "Not the primary interface on record"

            interface_fields = dict(filter(can_update, primary_network.items()))
            for field in interface_fields:
                if interface[field] != primary_network[field] : changed_fields.append('Interface.'+field)
            interface.update(interface_fields)
            interface.sync(commit = False)

        # indicate that node has booted & contacted PLC.
        node.update_last_contact()

        node.sync(commit = True)

        if changed_fields:
            self.message = "Boot updated: %s" % ", ".join(changed_fields)
            self.event_objects = { 'Node' : [node['node_id']] }

        return 1
