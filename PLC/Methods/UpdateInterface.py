from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.Interfaces import Interface, Interfaces
from PLC.Auth import Auth

can_update = lambda (field, value): field not in \
             ['interface_id','node_id']

class UpdateInterface(Method):
    """
    Updates an existing node network. Any values specified in
    interface_fields are used, otherwise defaults are
    used. Acceptable values for method are dhcp and static. If type is
    static, then ip, gateway, network, broadcast, netmask, and dns1
    must all be specified in interface_fields. If type is dhcp,
    these parameters, even if specified, are ignored.
    
    PIs and techs may only update networks associated with their own
    nodes. Admins may update any node network.
 
    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    interface_fields = dict(filter(can_update, Interface.fields.items()))

    accepts = [
        Auth(),
	Interface.fields['interface_id'],
     	interface_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, interface_id, interface_fields):
        interface_fields = dict(filter(can_update, interface_fields.items()))

	# Get node network information
	interfaces = Interfaces(self.api, [interface_id])
	if not interfaces:
            raise PLCInvalidArgument, "No such node network"

	interface = interfaces[0]
		
        # Authenticated function
        assert self.caller is not None

	# If we are not an admin, make sure that the caller is a
        # member of the site where the node exists.
        if 'admin' not in self.caller['roles']:
            nodes = Nodes(self.api, [interface['node_id']])
            if not nodes:
                raise PLCPermissionDenied, "Node network is not associated with a node"
            node = nodes[0]
            if node['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to update node network"

	# Update node network
	interface.update(interface_fields)
        interface.sync()
	
	self.event_objects = {'Interface': [interface['interface_id']]}
	self.message = "Node network %d updated: %s " % \
	    (interface['interface_id'], ", ".join(interface_fields.keys()))

        return 1
