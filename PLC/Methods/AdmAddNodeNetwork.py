from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.NodeNetworks import NodeNetwork, NodeNetworks
from PLC.Sites import Site, Sites
from PLC.Auth import PasswordAuth

class AdmAddNodeNetwork(Method):
    """
    Adds a new newtwork for a node. Any values specified in optional_vals are used,
    otherwise defaults are used. Acceptable values for method are dhcp, static, 
    proxy, tap, and ipmi. Acceptable value for type is ipv4. If type is static, 
    the parameter optional_vals must be present and ip, gateway, network, broadcast, 
    netmask, and dns1 must all be specified. If type is dhcp, these parameters, even 
    if specified, are ignored. Returns the new nodenetwork_id (>0) if successful.

    PIs and techs may only add networks to their own nodes. Admins may
    add networks to any node.

    Returns the new nodenetwork_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    cant_update = lambda (field, value): field not in \
                 ['nodenetwork_id']
    update_fields = dict(filter(cant_update, NodeNetwork.all_fields.items()))

    accepts = [
        PasswordAuth(),
        NodeNetwork.all_fields['node_id'],
        NodeNetwork.all_fields['method'],
        NodeNetwork.all_fields['type'],
        update_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, node_id, method, type, optional_vals = {}):
        if filter(lambda field: field not in self.update_fields, optional_vals):
            raise PLCInvalidArgument, "Invalid fields specified"

        # check if node exists
        nodes = Nodes(self.api, [node_id], Node.extra_fields).values()
        if not nodes:
            raise PLCInvalidArgument, "No such node"
	node = nodes[0]
	
        # Make sure node network doesnt already exist
        nodenetworks = NodeNetworks(self.api).values()
	if nodenetworks:
		for nodenetwork in nodenetworks:
			if nodenetwork['node_id'] == node_id and nodenetwork['method'] == method and nodenetwork['type'] == type:
				raise PLCInvalidArgument, "Node Network already exists"

        # Authenticated function
        assert self.caller is not None

        # If we are not an admin, make sure that the caller is a
        # member of the site where the node exists.
        if 'admin' not in self.caller['roles']:
        	if node['site_id'] not in self.caller['site_ids']:
            		raise PLCPermissionDenied, "Not allowed to add node network for specified node"
		if 'tech' not in self.caller['roles']:
			raise PLCPermissionDenied, "Not allowed to add node network for specified node"
	

        # add node network
	nodenetwork = NodeNetwork(self.api, optional_vals)
        nodenetwork['node_id'] = node_id
	nodenetwork['method'] = method
        nodenetwork['type'] = type
        nodenetwork.flush()

        return nodenetwork['nodenetwork_id']
