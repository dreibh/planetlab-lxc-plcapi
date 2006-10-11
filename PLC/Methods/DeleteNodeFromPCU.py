from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.PCUs import PCU, PCUs
from PLC.Auth import PasswordAuth

class DeleteNodeFromPCU(Method):
    """
    Deletes a node from a PCU.

    Non-admins may only update PCUs at their sites.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    accepts = [
        PasswordAuth(),
	Mixed(Node.fields['node_id'],
              Node.fields['hostname']),
        PCU.fields['pcu_id']
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, node_id_or_hostname, pcu_id):
	 # Get node
        nodes = Nodes(self.api, [node_id_or_hostname])
        if not nodes:
            raise PLCInvalidArgument, "No such node"

        node = nodes.values()[0]

        # Get PCU
        pcus = PCUs(self.api, [pcu_id])
        if not pcus:
            raise PLCInvalidArgument, "No such PCU"

        pcu = pcus.values()[0]

        if 'admin' not in self.caller['roles']:
            ok = False
            sites = Sites(self.api, self.caller['site_ids']).values()
            for site in sites:
                if pcu['pcu_id'] in site['pcu_ids']:
                    ok = True
                    break
            if not ok:
                raise PLCPermissionDenied, "Not allowed to update that PCU"
	
	# Removed node from PCU
        if node['node_id'] in pcu['node_ids']:
            pcu.remove_node(node)

        return 1
