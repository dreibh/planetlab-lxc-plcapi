from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.PCUs import PCU, PCUs
from PLC.Auth import Auth
from PLC.Methods.AddNodeToPCU import AddNodeToPCU

class AdmAssociateNodeToPowerControlUnitPort(AddNodeToPCU):
    """
    Deprecated. See AddNodeToPCU.
    """

    status = "deprecated"

    roles = ['admin', 'pi', 'tech']

    accepts = [
        Auth(),
        PCU.fields['pcu_id'],
        Parameter(int, 'PCU port number'),
	Mixed(Node.fields['node_id'],
              Node.fields['hostname']),
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, pcu_id, port, node_id_or_hostname):
        return AddNodeToPCU(self, auth, node_id_or_hostname, pcu_id, port)
