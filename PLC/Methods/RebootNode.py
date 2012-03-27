import socket

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.Interfaces import Interface, Interfaces
from PLC.Auth import Auth
from PLC.POD import udp_pod

class RebootNode(Method):
    """
    Sends the specified node a specially formatted UDP packet which
    should cause it to reboot immediately.

    Admins can reboot any node. Techs and PIs can only reboot nodes at
    their site.

    Returns 1 if the packet was successfully sent (which only whether
    the packet was sent, not whether the reboot was successful).
    """

    roles = ['admin', 'pi', 'tech']

    accepts = [
        Auth(),
        Mixed(Node.fields['node_id'],
              Node.fields['hostname'])
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, node_id_or_hostname):
        # Get account information
        nodes = Nodes(self.api, [node_id_or_hostname])
        if not nodes:
            raise PLCInvalidArgument, "No such node"

        node = nodes[0]

        # Authenticated function
        assert self.caller is not None

        # If we are not an admin, make sure that the caller is a
        # member of the site at which the node is located.
        if 'admin' not in self.caller['roles']:
            if node['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to delete nodes from specified site"

        session = node['session']
        if not session:
            raise PLCInvalidArgument, "No session key on record for that node (i.e., has never successfully booted)"
        session = session.strip()

        # Only use the hostname as a backup, try to use the primary ID
        # address instead.
        host = node['hostname']
        interfaces = Interfaces(self.api, node['interface_ids'])
        for interface in interfaces:
            if interface['is_primary'] == 1:
                host = interface['ip']
                break

        try:
            udp_pod(host, session)
        except socket.error, e:
            # Ignore socket errors
            pass

        self.event_objects = {'Node': [node['node_id']]}
        self.message = "RebootNode called"

        return 1
