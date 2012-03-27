import socket

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.Nodes import Node, Nodes
from PLC.PCUs import PCU, PCUs

try:
    from pcucontrol import reboot
    external_dependency = True
except:
    external_dependency = False

class RebootNodeWithPCU(Method):
    """
        Uses the associated PCU to attempt to reboot the given Node.

    Admins can reboot any node. Techs and PIs can only reboot nodes at
    their site.

    Returns 1 if the reboot proceeded without error (Note: this does not guarantee
        that the reboot is successful).
        Returns -1 if external dependencies for this call are not available.
        Returns "error string" if the reboot failed with a specific message.
    """

    roles = ['admin', 'pi', 'tech']

    accepts = [
        Auth(),
        Mixed(Node.fields['node_id'],
              Node.fields['hostname']),
        Parameter(bool, "Run as a test, or as a real reboot", nullok = True)
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, node_id_or_hostname, testrun=None):
    # Get account information
        nodes = Nodes(self.api, [node_id_or_hostname])
        if not nodes:
            raise PLCInvalidArgument, "No such node"

        if testrun is None:
            testrun = False

        node = nodes[0]

        # Authenticated function
        assert self.caller is not None

        # If we are not an admin, make sure that the caller is a
        # member of the site at which the node is located.
        if 'admin' not in self.caller['roles']:
            if node['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to reboot nodes from specified site"

        # Verify that the node has pcus associated with it.
        pcus = PCUs(self.api, {'pcu_id' : node['pcu_ids']} )
        if not pcus:
            raise PLCInvalidArgument, "No PCUs associated with Node"

        pcu = pcus[0]

        if not external_dependency:
            raise PLCNotImplemented, "Could not load external module to attempt reboot"

        # model, hostname, port,
        # i = pcu['node_ids'].index(node['node_id'])
        # p = pcu['ports'][i]
        ret = reboot.reboot_api(node, pcu, testrun)

        node.update_last_pcu_reboot(commit=True) # commits new timestamp to node 

        self.event_objects = {'Node': [node['node_id']]}
        self.message = "RebootNodeWithPCU %s with %s returned %s" % (node['node_id'], pcu['pcu_id'], ret)

        return ret
