from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.PCUProtocolTypes import PCUProtocolType, PCUProtocolTypes
from PLC.Auth import Auth

class DeletePCUProtocolType(Method):
    """
    Deletes a PCU protocol type.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        PCUProtocolType.fields['pcu_protocol_type_id']
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, protocol_type_id):
        protocol_types = PCUProtocolTypes(self.api, [protocol_type_id])
        if not protocol_types:
            raise PLCInvalidArgument, "No such pcu protocol type"

        protocol_type = protocol_types[0]
        protocol_type.delete()
        self.event_objects = {'PCUProtocolType': [protocol_type['pcu_protocol_type_id']]}

        return 1
