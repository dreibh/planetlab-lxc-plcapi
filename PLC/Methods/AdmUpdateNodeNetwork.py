
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.NodeNetworks import NodeNetwork, NodeNetworks
from PLC.Auth import PasswordAuth

class AdmUpdateNodeNetwork(Method):
    """
    Updates an existing node network. Any values specified in optional_vals 
    are used, otherwise defaults are used. Acceptable values for method are
    dhcp and static. If type is static, the parameter optional_vals must
    be present and ip, gateway, network, broadcast, netmask, and dns1 must
    all be specified. If type is dhcp, these parameters, even if
    specified, are ignored.
    
    PIs and techs may only add networks to their own nodes. Admins may
    add networks to any node.
 
    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    cant_update = lambda (field, value): field not in \
                 ['nodenetwork_id']
    update_fields = dict(filter(cant_update, NodeNetwork.all_fields.items()))

    accepts = [
        PasswordAuth(),
	Mixed(NodeNetwork.fields['nodenetwork_id'],
	      NodeNetwork.fields['hostname']),
     	update_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, nodenetwork_id_or_hostname, optional_vals=None):
        if filter(lambda field: field not in self.update_fields, optional_vals):
		raise PLCInvalidArgument, "Invalid fields specified"

        # Authenticated function
        assert self.caller is not None

	# Get nodenetwork information
	nodenetworks = NodeNetworks(self.api, [nodenetwork_id_or_hostname]).values()
	if not nodenetworks:
		raise PLCInvalidArgument, "No such node network"
	nodenetwork = nodenetworks[0]

	# Get Node using this node network
	#nodes = Nodes(self.api, [nodenetwork['node_id']]).values()
	#if not nodes:
	#	raise PLCPermissionDenied, "Node network is not associated with a node"
	#node = nodes[0]
	
	
	# If we are not an admin, make sure that the caller is a
        # member of the site where the node exists.
        if 'admin' not in self.caller['roles']:
		nodes = Nodes(self.api, [nodenetwork['node_id']]).values()
        	if not nodes:
                	raise PLCPermissionDenied, "Node network is not associated with a node"
        	node = nodes[0]
                if node['site_id'] not in self.caller['site_ids']:
                        raise PLCPermissionDenied, "Not allowed to update node network"
		if 'tech' not in self.caller['roles']:
			raise PLCPermissionDenied, "User account not allowed to update node network"
	
	# Update node network
	nodenetwork.update(optional_vals)
        nodenetwork.flush()
	
        return 1
