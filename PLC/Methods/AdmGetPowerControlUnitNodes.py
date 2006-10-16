from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.PCUs import PCU, PCUs
from PLC.Auth import PasswordAuth
from PLC.Methods.GetPCUs import GetPCUs

class AdmGetPowerControlUnitNodes(GetPCUs):
    """
    Deprecated. See GetPCUs.

    Returns a list of the nodes, and the ports they are assigned to,
    on the specified PCU.
    
    Admin may query all PCUs. Non-admins may only query the PCUs at
    their sites.
    """

    roles = ['admin', 'pi', 'tech']

    accepts = [
        PasswordAuth(),
        PCU.fields['pcu_id']
        ]

    returns = [{'node_id': Parameter(int, "Node identifier"),
                'port_number': Parameter(int, "Port number")}]

    def call(self, auth, pcu_id):
        pcus = GetPCUs.call(self, auth, [pcu_id])
        if not pcus:
            raise PLCInvalidArgument, "No such PCU"
        pcu = pcus[0]

        return [{'node_id': node_id, 'port_number': port} \
                for (node_id, port) in zip(pcu['node_ids'], pcu['ports'])]
