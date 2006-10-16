import os

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.Auth import PasswordAuth

class GetNodes(Method):
    """
    Return an array of dictionaries containing details about the
    specified nodes.

    If return_fields is specified, only the specified fields will be
    returned. Only admins may retrieve certain fields. Otherwise, the
    default set of fields returned is:

    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        [Mixed(Node.fields['node_id'],
               Node.fields['hostname'])],
        ]

    returns = [Node.fields]

    def __init__(self, *args, **kwds):
        Method.__init__(self, *args, **kwds)
        # Update documentation with list of default fields returned
        self.__doc__ += os.linesep.join(Node.fields.keys())

    def call(self, auth, node_id_or_hostname_list = None):
        # Authenticated function
        assert self.caller is not None

        valid_fields = Node.fields.keys()

        # Remove admin only fields
        if 'admin' not in self.caller['roles']:
            for key in ['boot_nonce', 'key', 'session', 'root_person_ids']:
                valid_fields.remove(key)

        # Get node information
        nodes = Nodes(self.api, node_id_or_hostname_list).values()

        # turn each node into a real dict.
        nodes = [dict(node) for node in nodes]
                    
        return nodes
