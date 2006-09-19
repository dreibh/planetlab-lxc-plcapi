from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.Auth import PasswordAuth

class AdmUpdateNode(Method):
    """
    Updates a node. Only the fields specified in update_fields are
    updated, all other fields are left untouched.

    To remove a value without setting a new one in its place (for
    example, to remove an address from the node), specify -1 for int
    and double fields and 'null' for string fields. hostname and
    boot_state cannot be unset.
    
    PIs and techs can only update the nodes at their sites.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    can_update = lambda (field, value): field in \
                 ['hostname', 'boot_state', 'model', 'version']
    update_fields = dict(filter(can_update, Node.fields.items()))

    accepts = [
        PasswordAuth(),
        Mixed(Node.fields['node_id'],
              Node.fields['hostname']),
        update_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, node_id_or_hostname, update_fields):
        if filter(lambda field: field not in self.update_fields, update_fields):
            raise PLCInvalidArgument, "Invalid field specified"

        # XML-RPC cannot marshal None, so we need special values to
        # represent "unset".
        for key, value in update_fields.iteritems():
            if value == -1 or value == "null":
                if key in ['hostname', 'boot_state']:
                    raise PLCInvalidArgument, "hostname and boot_state cannot be unset"
                update_fields[key] = None

        # Get account information
        nodes = Nodes(self.api, [node_id_or_hostname])
        if not nodes:
            raise PLCInvalidArgument, "No such node"

        node = nodes.values()[0]

        # Authenticated function
        assert self.caller is not None

        # If we are not an admin, make sure that the caller is a
        # member of the site at which the node is located.
        if 'admin' not in self.caller['roles']:
            if node['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to delete nodes from specified site"

        # Check if we can update this account
        node = nodes.values()[0]
        if not self.caller.can_update(node):
            raise PLCPermissionDenied, "Not allowed to update specified account"

        node.update(update_fields)
        node.flush()

        return 1
