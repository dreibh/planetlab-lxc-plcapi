from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.PCUs import PCU, PCUs
from PLC.Auth import PasswordAuth

class AddNodeToPCU(Method):
    """
    Adds a node to a port on a PCU. Faults if the node has already
    been added to the PCU or if the port is already in use.

    Non-admins may only update PCUs at their sites.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    accepts = [
        PasswordAuth(),
	Mixed(Node.fields['node_id'],
              Node.fields['hostname']),
        PCU.fields['pcu_id'],
        Parameter(int, 'PCU port number')
        ]

    returns = Parameter(int, '1 if successful')
    event_type = 'AddTo'
    object_type = 'PCU'
    object_ids = []

    def call(self, auth, node_id_or_hostname, pcu_id, port):
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
	
	# Add node to PCU
        if node['node_id'] in pcu['node_ids']:
            raise PLCInvalidArgument, "Node already controlled by PCU"

        if port in pcu['ports']:
            raise PLCInvalidArgument, "PCU port already in use"

        pcu.add_node(node, port)
	self.object_ids = [pcu['pcu_id']]

        return 1
