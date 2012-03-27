from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.PCUTypes import PCUType, PCUTypes
from PLC.Auth import Auth

class DeletePCUType(Method):
    """
    Deletes a PCU type.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        PCUType.fields['pcu_type_id']
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, pcu_type_id):
        pcu_types = PCUTypes(self.api, [pcu_type_id])
        if not pcu_types:
            raise PLCInvalidArgument, "No such pcu type"

        pcu_type = pcu_types[0]
        pcu_type.delete()
        self.event_objects = {'PCUType': [pcu_type['pcu_type_id']]}

        return 1
