from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.PCUs import PCU, PCUs
from PLC.Auth import Auth
from PLC.Methods.DeleteNodeFromPCU import DeleteNodeFromPCU

class AdmDisassociatePowerControlUnitPort(DeleteNodeFromPCU):
    """
    Deprecated. See DeleteNodeFromPCU.
    """

    status = "deprecated"

    roles = ['admin', 'pi', 'tech']

    accepts = [
        Auth(),
        PCU.fields['pcu_id'],
        Parameter(int, 'PCU port number'),
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, pcu_id, port):
        pcus = PCUs(self.api, [pcu_id]).values()
        if not pcus:
            raise PLCInvalidArgument, "No such PCU"

        pcu = pcus.values()[0]

        ports = dict(zip(pcu['ports'], pcu['node_ids']))
        if port not in ports:
            raise PLCInvalidArgument, "No node on that port or no such port"

        return DeleteNodeFromPCU(self, auth, ports[port], pcu_id)
