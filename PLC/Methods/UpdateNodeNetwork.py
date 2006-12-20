from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.NodeNetworks import NodeNetwork, NodeNetworks
from PLC.Auth import Auth

can_update = lambda (field, value): field not in \
             ['nodenetwork_id']

class UpdateNodeNetwork(Method):
    """
    Updates an existing node network. Any values specified in
    nodenetwork_fields are used, otherwise defaults are
    used. Acceptable values for method are dhcp and static. If type is
    static, then ip, gateway, network, broadcast, netmask, and dns1
    must all be specified in nodenetwork_fields. If type is dhcp,
    these parameters, even if specified, are ignored.
    
    PIs and techs may only update networks associated with their own
    nodes. Admins may update any node network.
 
    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    nodenetwork_fields = dict(filter(can_update, NodeNetwork.fields.items()))

    accepts = [
        Auth(),
	NodeNetwork.fields['nodenetwork_id'],
     	nodenetwork_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, nodenetwork_id, nodenetwork_fields):
        nodenetwork_fields = dict(filter(can_update, nodenetwork_fields.items()))

	# Get node network information
	nodenetworks = NodeNetworks(self.api, [nodenetwork_id])
	if not nodenetworks:
            raise PLCInvalidArgument, "No such node network"

	nodenetwork = nodenetworks[0]
		
        # Authenticated function
        assert self.caller is not None

	# If we are not an admin, make sure that the caller is a
        # member of the site where the node exists.
        if 'admin' not in self.caller['roles']:
            nodes = Nodes(self.api, [nodenetwork['node_id']])
            if not nodes:
                raise PLCPermissionDenied, "Node network is not associated with a node"
            node = nodes[0]
            if node['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to update node network"

	# Update node network
	nodenetwork.update(nodenetwork_fields)
        nodenetwork.sync()
	
	self.object_ids = [nodenetwork['nodenetwork_id']]
	self.message = "Node network %d updated: %s " % \
	    (nodenetwork['nodenetwork_id'], ", ".join(nodenetwork_fields.keys()))

        return 1
