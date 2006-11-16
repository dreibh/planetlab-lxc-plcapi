from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.ForeignNodes import ForeignNode, ForeignNodes
from PLC.Slices import Slice, Slices
from PLC.Auth import Auth

class DeleteSliceFromNodes(Method):
    """
    Deletes the specified slice from the specified nodes. If the slice is
    not associated with a node, no errors are returned. 

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        Mixed(Slice.fields['slice_id'],
              Slice.fields['name']),
	[Mixed(Node.fields['node_id'],
               Node.fields['hostname'])]
        ]

    returns = Parameter(int, '1 if successful')

    event_type = 'DeleteFrom'
    object_type = 'Node'

    def call(self, auth, slice_id_or_name, node_id_or_hostname_list):
        # Get slice information
        slices = Slices(self.api, [slice_id_or_name])
        if not slices:
            raise PLCInvalidArgument, "No such slice"

        slice = slices[0]

        if 'admin' not in self.caller['roles']:
            if self.caller['person_id'] in slice['person_ids']:
                pass
            elif 'pi' not in self.caller['roles']:
                raise PLCPermissionDenied, "Not a member of the specified slice"
            elif slice['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Specified slice not associated with any of your sites"
	
	# Remove slice from all nodes found

	# Get specified nodes
        nodes = Nodes(self.api, node_id_or_hostname_list)
        foreign_nodes = ForeignNodes(self.api, node_id_or_hostname_list)
        all_nodes = nodes+foreign_nodes;
	for node in all_nodes:
            if slice['slice_id'] in node['slice_ids']:
                slice.remove_node(node, commit = False)

        slice.sync()
	
	self.object_ids = [node['node_id'] for node in all_nodes]

        return 1
