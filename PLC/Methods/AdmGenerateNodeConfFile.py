import random
import base64

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.NodeNetworks import NodeNetwork, NodeNetworks
from PLC.Auth import Auth

class AdmGenerateNodeConfFile(Method):
    """
    Deprecated. Functionality can be implemented with GetNodes,
    GetNodeNetworks, and UpdateNode.

    Creates a new node configuration file if all network settings are
    present. This function will generate a new node key for the
    specified node, effectively invalidating any old configuration
    files.

    Non-admins can only generate files for nodes at their sites.

    Returns the contents of the file if successful, faults otherwise.
    """

    status = "deprecated"

    roles = ['admin', 'pi', 'tech']

    accepts = [
        Auth(),
        Mixed(Node.fields['node_id'],
              Node.fields['hostname'])
        ]

    returns = Parameter(str, "Node configuration file")

    def call(self, auth, node_id_or_hostname):
        # Get node information
        nodes = Nodes(self.api, [node_id_or_hostname]).values()
        if not nodes:
            raise PLCInvalidArgument, "No such node"
        node = nodes[0]

        # If we are not an admin, make sure that the caller is a
        # member of the site at which the node is located.
        if 'admin' not in self.caller['roles']:
            if node['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to generate a configuration file for that node"

	# Get node networks for this node
        primary = None
        nodenetworks = NodeNetworks(self.api, node['nodenetwork_ids']).values()
        for nodenetwork in nodenetworks:
            if nodenetwork['is_primary']:
                primary = nodenetwork
                break
        if primary is None:
            raise PLCInvalidArgument, "No primary network configured"

        # Split hostname into host and domain parts
        parts = node['hostname'].split(".", 1)
        if len(parts) < 2:
            raise PLCInvalidArgument, "Node hostname is invalid"
        host = parts[0]
        domain = parts[1]

        # Generate 32 random bytes
        bytes = random.sample(xrange(0, 256), 32)
        # Base64 encode their string representation
        node['key'] = base64.b64encode("".join(map(chr, bytes)))
        # XXX Boot Manager cannot handle = in the key
        node['key'] = node['key'].replace("=", "")
        # Save it
        node.sync()

        # Generate node configuration file suitable for BootCD
        file = ""

        file += 'NODE_ID="%d"\n' % node['node_id']
        file += 'NODE_KEY="%s"\n' % node['key']

        if primary['mac']:
            file += 'NET_DEVICE="%s"\n' % primary['mac'].lower()

        file += 'IP_METHOD="%s"\n' % primary['method']

        if primary['method'] == 'static':
            file += 'IP_ADDRESS="%s"\n' % primary['ip']
            file += 'IP_GATEWAY="%s"\n' % primary['gateway']
            file += 'IP_NETMASK="%s"\n' % primary['netmask']
            file += 'IP_NETADDR="%s"\n' % primary['network']
            file += 'IP_BROADCASTADDR="%s"\n' % primary['broadcast']
            file += 'IP_DNS1="%s"\n' % primary['dns1']
            file += 'IP_DNS2="%s"\n' % (primary['dns2'] or "")

        file += 'HOST_NAME="%s"\n' % host
        file += 'DOMAIN_NAME="%s"\n' % domain

        for nodenetwork in nodenetworks:
            if nodenetwork['method'] == 'ipmi':
                file += 'IPMI_ADDRESS="%s"\n' % nodenetwork['ip']
                if nodenetwork['mac']:
                    file += 'IPMI_MAC="%s"\n' % nodenetwork['mac'].lower()
                break

        return file
