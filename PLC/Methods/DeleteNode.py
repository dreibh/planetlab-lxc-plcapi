from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth
from PLC.Nodes import Node, Nodes

class DeleteNode(Method):
    """
    Mark an existing node as deleted.

    PIs and techs may only delete nodes at their own sites. ins may
    delete nodes at any site.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    accepts = [
        Auth(),
        Mixed(Node.fields['node_id'],
              Node.fields['hostname'])
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, node_id_or_hostname):
        # Get account information
        nodes = Nodes(self.api, [node_id_or_hostname])
        if not nodes:
            raise PLCInvalidArgument, "No such node"
        node = nodes[0]

        if node['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local node"

        # If we are not an admin, make sure that the caller is a
        # member of the site at which the node is located.
        if 'admin' not in self.caller['roles']:
            # Authenticated function
            assert self.caller is not None

            if node['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to delete nodes from specified site"

        node_id=node['node_id']
        site_id=node['site_id']
        node.delete()

        # Logging variables
        # it's not much use to attach to the node as it's going to vanish...
        self.event_objects = {'Node': [node_id], 'Site': [site_id] }
        self.message = "Node %d deleted" % node['node_id']

        return 1
