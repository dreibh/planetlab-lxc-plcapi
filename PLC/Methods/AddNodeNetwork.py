from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.NodeNetworks import NodeNetwork, NodeNetworks
from PLC.Auth import PasswordAuth

can_update = lambda (field, value): field not in ['nodenetwork_id']

class AddNodeNetwork(Method):
    """
    Adds a new network for a node. Any values specified in
    nodenetwork_fields are used, otherwise defaults are used. Acceptable
    values for method are dhcp, static, proxy, tap, and
    ipmi. Acceptable value for type is ipv4. If type is static, ip,
    gateway, network, broadcast, netmask, and dns1 must all be
    specified in nodenetwork_fields. If type is dhcp, these parameters,
    even if specified, are ignored.

    PIs and techs may only add networks to their own nodes. ins may
    add networks to any node.

    Returns the new nodenetwork_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    nodenetwork_fields = dict(filter(can_update, NodeNetwork.fields.items()))

    accepts = [
        PasswordAuth(),
        nodenetwork_fields
        ]

    returns = Parameter(int, 'New nodenetwork_id (> 0) if successful')

    event_type = 'Add'
    object_type = 'NodeNetwork'
    object_ids = []

    def call(self, auth, nodenetwork_fields = {}):
        nodenetwork_fields = dict(filter(can_update, nodenetwork_fields.items()))

        # Check if node exists
        nodes = Nodes(self.api, [nodenetwork_fields['node_id']]).values()
        if not nodes:
            raise PLCInvalidArgument, "No such node"
	node = nodes[0]

        # Authenticated function
        assert self.caller is not None

        # If we are not an admin, make sure that the caller is a
        # member of the site where the node exists.
        if 'admin' not in self.caller['roles']:
            if node['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to add node network for specified node"

        # Add node network
	nodenetwork = NodeNetwork(self.api, nodenetwork_fields)
        nodenetwork.sync()

	self.object_ids = [node['node_id'], nodenetwork['nodenetwork_id']]	

        return nodenetwork['nodenetwork_id']
