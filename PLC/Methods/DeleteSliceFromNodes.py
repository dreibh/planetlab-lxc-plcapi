from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.Slices import Slice, Slices
from PLC.Auth import PasswordAuth

class DeleteSliceFromNodes(Method):
    """
    Deletes the specified slice from the specified nodes. If the slice is
    not associated with a node, no errors are returned. 

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi']

    accepts = [
        PasswordAuth(),
        Mixed(Slice.fields['slice_id'],
              Slice.fields['name']),
	[Mixed(Node.fields['node_id'],
               Node.fields['hostname'])]
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, slice_id_or_name, node_id_or_hostname_list):

        # Get slice information
        slices = Slices(self.api, [slice_id_or_name])
        if not slices:
            raise PLCInvalidArgument, "No such slice"

        slice = slices.values()[0]

	# Get specified nodes
        nodes = Nodes(self.api, node_id_or_hostname_list).values()

        # If we are not admin, make sure the caller is a pi
        # of the site associated with the slice
	if 'admin' not in self.caller['roles']:
		if slice['site_id'] not in self.caller['site_ids']:
			raise PLCPermissionDenied, "Not allowed to delete nodes from this slice"
	
	# add slice to all nodes found
	for node in nodes:
		if slice['slice_id'] in node['slice_ids']:
            		slice.remove_node(node)

        return 1
