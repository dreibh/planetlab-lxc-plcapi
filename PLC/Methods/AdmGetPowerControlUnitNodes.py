from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.PCUs import PCU, PCUs
from PLC.Auth import PasswordAuth

class AdmGetPowerControlUnitNodes(Method):
    """
    Deprecated. See GetPCUs.

    Returns a list of the nodes, and the ports they are assigned to,
    on the specified PCU.
    
    Admin may query all PCUs. Non-admins may only query the PCUs at
    their sites.
    """

    status = "deprecated"

    roles = ['admin', 'pi', 'tech']

    accepts = [
        PasswordAuth(),
        PCU.fields['pcu_id']
        ]

    returns = [{'node_id': Parameter(int, "Node identifier"),
                'port_number': Parameter(int, "Port number")}]

    def call(self, auth, pcu_id):
        pcus = PCUs(self.api, [pcu_id]).values()
        if not pcus:
            raise PLCInvalidArgument, "No such PCU"
        pcu = pcus[0]

        if 'admin' not in self.caller['roles']:
            if pcu['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to view that PCU"

        return [{'node_id': node_id, 'port_number': port} \
                for (node_id, port) in zip(pcu['node_ids'], pcu['ports'])]
