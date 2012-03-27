from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.Slices import Slice, Slices
from PLC.Auth import Auth

class AddSliceToNodesWhitelist(Method):
    """
    Adds the specified slice to the whitelist on the specified nodes. Nodes may be
    either local or foreign nodes.

    If the slice is already associated with a node, no errors are
    returned.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
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
        slice = slices[0]

        if slice['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local slice"

        # Get specified nodes, add them to the slice
        nodes = Nodes(self.api, node_id_or_hostname_list)
        for node in nodes:
            if node['peer_id'] is not None:
                raise PLCInvalidArgument, "%s not a local node" % node['hostname']
            if slice['slice_id'] not in node['slice_ids_whitelist']:
                slice.add_to_node_whitelist(node, commit = False)

        slice.sync()

        self.event_objects = {'Node': [node['node_id'] for node in nodes],
                              'Slice': [slice['slice_id']]}

        return 1
