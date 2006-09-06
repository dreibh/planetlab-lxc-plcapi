from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import PasswordAuth
from PLC.Nodes import Node, Nodes

class AdmDeleteNode(Method):
    """
    Mark an existing node as deleted.

    PIs and techs may only delete nodes at their own sites. Admins may
    delete nodes at any site.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    accepts = [
        PasswordAuth(),
        Mixed(Node.fields['node_id'],
              Node.fields['hostname'])
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, node_id_or_hostname):
        # Get account information
        nodes = Nodes(self.api, [node_id_or_hostname])
        if not nodes:
            raise PLCInvalidArgument, "No such node"

        node = nodes.values()[0]

        # If we are not an admin, make sure that the caller is a
        # member of the site at which the node is located.
        if 'admin' not in self.caller['roles']:
            # Authenticated function
            assert self.caller is not None

            if node['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to delete nodes from specified site"

        node.delete()

        return 1
