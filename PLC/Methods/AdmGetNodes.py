import os

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.Auth import PasswordAuth

class AdmGetNodes(Method):
    """
    Return an array of dictionaries containing details about the
    specified accounts.

    Admins may retrieve details about all accounts by not specifying
    node_id_or_email_list or by specifying an empty list. Users and
    techs may only retrieve details about themselves. PIs may retrieve
    details about themselves and others at their sites.

    If return_fields is specified, only the specified fields will be
    returned, if set. Otherwise, the default set of fields returned is:

    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        [Mixed(Node.fields['node_id'],
               Node.fields['hostname'])],
        Parameter([str], 'List of fields to return')
        ]

    # Filter out hidden fields
    can_return = lambda (field, value): field not in ['deleted']
    return_fields = dict(filter(can_return, Node.all_fields.items()))
    returns = [return_fields]

    def __init__(self, *args, **kwds):
        Method.__init__(self, *args, **kwds)
        # Update documentation with list of default fields returned
        self.__doc__ += os.linesep.join(Node.default_fields.keys())

    def call(self, auth, node_id_or_hostname_list = None, return_fields = None):
        # Authenticated function
        assert self.caller is not None

        # Remove admin only fields
        if 'admin' not in self.caller['roles']:
            for key in ['boot_nonce', 'key', 'session', 'root_person_ids']:
                del self.return_fields[key]

        # Make sure that only valid fields are specified
        if return_fields is None:
            return_fields = self.return_fields
        elif filter(lambda field: field not in self.return_fields, return_fields):
            raise PLCInvalidArgument, "Invalid return field specified"

        # Get node information
        nodes = Nodes(self.api, node_id_or_hostname_list, return_fields).values()

        # Filter out undesired or None fields (XML-RPC cannot marshal
        # None) and turn each node into a real dict.
        valid_return_fields_only = lambda (key, value): \
                                   key in return_fields and value is not None
        nodes = [dict(filter(valid_return_fields_only, node.items())) \
                 for node in nodes]
                    
        return nodes
