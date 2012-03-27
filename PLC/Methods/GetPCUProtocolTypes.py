from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.PCUProtocolTypes import PCUProtocolType, PCUProtocolTypes
from PLC.Auth import Auth
from PLC.Filter import Filter

class GetPCUProtocolTypes(Method):
    """
    Returns an array of PCU Types.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node']

    accepts = [
        Auth(),
        Mixed([PCUProtocolType.fields['pcu_type_id']],
               Filter(PCUProtocolType.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [PCUProtocolType.fields]


    def call(self, auth, protocol_type_filter = None, return_fields = None):

        #Must query at least pcu_type_id
        if return_fields is not None and 'pcu_protocol_type_id' not in return_fields:
            return_fields.append('pcu_protocol_type_id')
            added_fields = ['pcu_protocol_type_id']
        else:
            added_fields = []

        protocol_types = PCUProtocolTypes(self.api, protocol_type_filter, return_fields)

        for added_field in added_fields:
            for protocol_type in protocol_types:
                del protocol_type[added_field]

        return protocol_types
