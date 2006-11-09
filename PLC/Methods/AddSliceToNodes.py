from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.ForeignNodes import ForeignNode, ForeignNodes
from PLC.Slices import Slice, Slices
from PLC.Auth import Auth

class AddSliceToNodes(Method):
    """
    Adds the specified slice to the specified nodes.
    Nodes can be either regular (local) nodes as returned by GetNodes
    or foreign nodes as returned by GetForeignNodes

    If the slice is
    already associated with a node, no errors are returned. 

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

    event_type = 'AddTo'
    object_type = 'Node'
    object_ids = []

    def call(self, auth, slice_id_or_name, node_id_or_hostname_list):
        # Get slice information
        slices = Slices(self.api, [slice_id_or_name])
        if not slices:
            raise PLCInvalidArgument, "No such slice"

        slice = slices[0]

        if 'admin' not in self.caller['roles']:
            if self.caller['person_id'] in slice['person_ids']:
                pass
            # Thierry : I cannot figure out how this works
            # how is having pi role related to being in a slice ?
            elif 'pi' not in self.caller['roles']:
                raise PLCPermissionDenied, "Not a member of the specified slice"
            elif slice['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Specified slice not associated with any of your sites"
	
	 # Get specified nodes, and them to the slice
        nodes = Nodes(self.api, node_id_or_hostname_list)
	for node in nodes:
            if slice['slice_id'] not in node['slice_ids']:
                slice.add_node(node, commit = False)

        # the same for foreign_nodes
        foreign_nodes = ForeignNodes (self.api, node_id_or_hostname_list)
        for foreign_node in foreign_nodes:
            if slice['slice_id'] not in foreign_node['slice_ids']:
                slice.add_node (foreign_node, is_foreign_node=True, commit=False)

        slice.sync()

	self.object_ids = [node['node_id'] for node in nodes]

        return 1
