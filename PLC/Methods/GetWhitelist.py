from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Nodes import Node, Nodes
from PLC.Persons import Person, Persons
from PLC.Auth import Auth

class GetWhitelist(Method):
    """
    Returns an array of structs containing details about the specified nodes
    whitelists. If node_filter is specified and is an array of node identifiers or
    hostnames, or a struct of node attributes, only nodes matching the
    filter will be returned. If return_fields is specified, only the
    specified details will be returned.

    Some fields may only be viewed by admins.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node', 'anonymous']

    accepts = [
        Auth(),
        Mixed([Mixed(Node.fields['node_id'],
                     Node.fields['hostname'])],
              Filter(Node.fields)),
        Parameter([str], "List of fields to return", nullok = True),
        ]

    returns = [Node.fields]


    def call(self, auth, node_filter = None, return_fields = None):

        # Must query at least slice_ids_whitelist
        if return_fields is not None:
            added_fields = set(['slice_ids_whitelist']).difference(return_fields)
            return_fields += added_fields
        else:
            added_fields =[]

        # Get node information
        nodes = Nodes(self.api, node_filter, return_fields)

        # Remove all nodes without a whitelist
        for node in nodes[:]:
            if not node['slice_ids_whitelist']:
                nodes.remove(node)

        # Remove admin only fields
        if not isinstance(self.caller, Person) or \
           'admin' not in self.caller['roles']:
            slice_ids = set()
            if self.caller:
                slice_ids.update(self.caller['slice_ids'])
            #if node has whitelist, make sure the user has a slice on the whitelist
            for node in nodes[:]:
                if 'slice_ids_whitelist' in node and \
                   node['slice_ids_whitelist'] and \
                   not slice_ids.intersection(node['slice_ids_whitelist']):
                    nodes.remove(node)
            for node in nodes:
                for field in ['boot_nonce', 'key', 'session', 'root_person_ids']:
                    if field in node:
                        del node[field]

        # remove added fields if not specified
        if added_fields:
            for node in nodes:
                for field in added_fields:
                    del node[field]

        return nodes
