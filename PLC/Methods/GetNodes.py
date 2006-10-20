from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.Auth import PasswordAuth

class GetNodes(Method):
    """
    Return an array of structs containing details about nodes. If
    node_id_or_hostname_list is specified, only the specified nodes
    will be queried.

    Some fields may only be viewed by admins.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        [Mixed(Node.fields['node_id'],
               Node.fields['hostname'])],
        ]

    returns = [Node.fields]

    def call(self, auth, node_id_or_hostname_list = None):
        # Authenticated function
        assert self.caller is not None

        valid_fields = Node.fields.keys()

        # Remove admin only fields
        if 'admin' not in self.caller['roles']:
            for key in ['boot_nonce', 'key', 'session', 'root_person_ids']:
                if key in valid_fields:
                    valid_fields.remove(key)

        # Get node information
        nodes = Nodes(self.api, node_id_or_hostname_list).values()

        # Turn each node into a real dict
        nodes = [dict(node) for node in nodes]
                    
        return nodes
