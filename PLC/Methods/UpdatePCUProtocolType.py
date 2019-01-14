from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.PCUProtocolTypes import PCUProtocolType, PCUProtocolTypes
from PLC.Auth import Auth

can_update = lambda field_value: field_value[0] in \
             ['pcu_type_id', 'port', 'protocol', 'supported']

class UpdatePCUProtocolType(Method):
    """
    Updates a pcu protocol type. Only the fields specified in
    port_typee_fields are updated, all other fields are left untouched.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    protocol_type_fields = dict(list(filter(can_update, list(PCUProtocolType.fields.items()))))

    accepts = [
        Auth(),
        PCUProtocolType.fields['pcu_protocol_type_id'],
        protocol_type_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, protocol_type_id, protocol_type_fields):
        protocol_type_fields = dict(list(filter(can_update, list(protocol_type_fields.items()))))

        protocol_types = PCUProtocolTypes(self.api, [protocol_type_id])
        if not protocol_types:
            raise PLCInvalidArgument("No such pcu protocol type")

        protocol_type = protocol_types[0]
        protocol_type.update(protocol_type_fields)
        protocol_type.sync()
        self.event_objects = {'PCUProtocolType': [protocol_type['pcu_protocol_type_id']]}
        return 1
