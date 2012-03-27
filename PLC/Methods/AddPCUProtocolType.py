from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.PCUProtocolTypes import PCUProtocolType, PCUProtocolTypes
from PLC.PCUTypes import PCUType, PCUTypes
from PLC.Auth import Auth

can_update = lambda (field, value): field in \
             ['pcu_type_id', 'port', 'protocol', 'supported']

class AddPCUProtocolType(Method):
    """
    Adds a new pcu protocol type.

    Returns the new pcu_protocol_type_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin']

    protocol_type_fields = dict(filter(can_update, PCUProtocolType.fields.items()))

    accepts = [
        Auth(),
        Mixed(PCUType.fields['pcu_type_id'],
              PCUType.fields['model']),
        protocol_type_fields
        ]

    returns = Parameter(int, 'New pcu_protocol_type_id (> 0) if successful')

    def call(self, auth, pcu_type_id_or_model, protocol_type_fields):

        # Check if pcu type exists
        pcu_types = PCUTypes(self.api, [pcu_type_id_or_model])
        if not pcu_types:
            raise PLCInvalidArgument, "No such pcu type"
        pcu_type = pcu_types[0]


        # Check if this port is already used
        if 'port' not in protocol_type_fields:
            raise PLCInvalidArgument, "Must specify a port"
        else:
            protocol_types = PCUProtocolTypes(self.api, {'pcu_type_id': pcu_type['pcu_type_id']})
            for protocol_type in protocol_types:
                if protocol_type['port'] == protocol_type_fields['port']:
                    raise PLCInvalidArgument, "Port alreay in use"

        protocol_type_fields = dict(filter(can_update, protocol_type_fields.items()))
        protocol_type = PCUProtocolType(self.api, protocol_type_fields)
        protocol_type['pcu_type_id'] = pcu_type['pcu_type_id']
        protocol_type.sync()
        self.event_object = {'PCUProtocolType': [protocol_type['pcu_protocol_type_id']]}

        return protocol_type['pcu_protocol_type_id']
