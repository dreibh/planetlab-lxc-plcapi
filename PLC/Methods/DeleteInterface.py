from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth
from PLC.Nodes import Node, Nodes
from PLC.Interfaces import Interface, Interfaces

class DeleteInterface(Method):
    """
    Deletes an existing interface.

    Admins may delete any interface. PIs and techs may only delete
    interface interfaces associated with nodes at their sites.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    accepts = [
        Auth(),
        Interface.fields['interface_id']
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, interface_id):

        # Get interface information
        interfaces = Interfaces(self.api, [interface_id])
        if not interfaces:
            raise PLCInvalidArgument, "No such interface %r"%interface_id
        interface = interfaces[0]

        # Get node information
        nodes = Nodes(self.api, [interface['node_id']])
        if not nodes:
            raise PLCInvalidArgument, "No such node %r"%node_id
        node = nodes[0]

        # Authenticated functino
        assert self.caller is not None

        # If we are not an admin, make sure that the caller is a
        # member of the site at which the node is located.
        if 'admin' not in self.caller['roles']:
            if node['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to delete this interface"

        interface.delete()

        # Logging variables
        self.event_objects = {'Interface': [interface['interface_id']]}
        self.message = "Interface %d deleted" % interface['interface_id']

        return 1
