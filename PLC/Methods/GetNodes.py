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
        Parameter([str], 'List of fields to return')
        ]

    returns = [Node.fields]

    def __init__(self, *args, **kwds):
        Method.__init__(self, *args, **kwds)
        # Update documentation with list of default fields returned
        self.__doc__ += os.linesep.join(Node.fields.keys())

    def call(self, auth, node_id_or_hostname_list = None, return_fields = None):
        # Authenticated function
        assert self.caller is not None

        valid_fields = Node.fields.keys()

        # Remove admin only fields
        if 'admin' not in self.caller['roles']:
            for key in ['boot_nonce', 'key', 'session', 'root_person_ids']:
                valid_fields.remove(key)

        # Make sure that only valid fields are specified
        if return_fields is None:
            return_fields = valid_fields
        elif filter(lambda field: field not in valid_fields, return_fields):
            raise PLCInvalidArgument, "Invalid return field specified"

        # Get node information
        nodes = Nodes(self.api, node_id_or_hostname_list).values()

        # Filter out undesired or None fields (XML-RPC cannot marshal
        # None) and turn each node into a real dict.
        valid_return_fields_only = lambda (key, value): \
                                   key in return_fields and value is not None
        nodes = [dict(filter(valid_return_fields_only, node.items())) \
                 for node in nodes]
                    
        return nodes
