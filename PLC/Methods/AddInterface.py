from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.Interfaces import Interface, Interfaces
from PLC.Auth import Auth

can_update = lambda (field, value): field not in ['interface_id', 'node_id']

class AddInterface(Method):
    """

    Adds a new network for a node. Any values specified in
    interface_fields are used, otherwise defaults are
    used. Acceptable values for method may be retrieved via
    GetNetworkMethods. Acceptable values for type may be retrieved via
    GetNetworkTypes.

    If type is static, ip, gateway, network, broadcast, netmask, and
    dns1 must all be specified in interface_fields. If type is dhcp,
    these parameters, even if specified, are ignored.

    PIs and techs may only add networks to their own nodes. Admins may
    add networks to any node.

    Returns the new interface_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    interface_fields = dict(filter(can_update, Interface.fields.items()))

    accepts = [
        Auth(),
        Mixed(Node.fields['node_id'],
              Node.fields['hostname']),
        interface_fields
        ]

    returns = Parameter(int, 'New interface_id (> 0) if successful')

    
    def call(self, auth, node_id_or_hostname, interface_fields):
        interface_fields = dict(filter(can_update, interface_fields.items()))

        # Check if node exists
        nodes = Nodes(self.api, [node_id_or_hostname])
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
	interface = Interface(self.api, interface_fields)
        interface['node_id'] = node['node_id']
	# if this is the first node network, make it primary
	if not node['interface_ids']:
		interface['is_primary'] = True
        interface.sync()
	
	# Logging variables
	self.object_ids = [node['node_id'], interface['interface_id']]	
	self.messgage = "Node network %d added" % interface['interface_id']

        return interface['interface_id']
