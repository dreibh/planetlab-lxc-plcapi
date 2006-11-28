from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Nodes import Node, Nodes
from PLC.Auth import Auth

class GetNodes(Method):
    """
    Returns an array of structs containing details about nodes. If
    node_filter is specified and is an array of node identifiers or
    hostnames, or a struct of node attributes, only nodes matching the
    filter will be returned. If return_fields is specified, only the
    specified details will be returned.

    Some fields may only be viewed by admins.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        Auth(),
        Mixed([Mixed(Node.fields['node_id'],
                     Node.fields['hostname'])],
              Filter(Node.fields)),
        Parameter([str], "List of fields to return", nullok = True),
        ]

    returns = [Node.fields]

    def call(self, auth, node_filter = None, return_fields = None):
        # Get node information
        nodes = Nodes(self.api, node_filter, return_fields)

        # Remove admin only fields
        if 'admin' not in self.caller['roles']:
            for node in nodes:
                for field in ['boot_nonce', 'key', 'session', 'root_person_ids']:
                    if field in node:
                        del node[field]

        return nodes
