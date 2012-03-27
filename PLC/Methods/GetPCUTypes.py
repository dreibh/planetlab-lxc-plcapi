from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.PCUTypes import PCUType, PCUTypes
from PLC.Auth import Auth
from PLC.Filter import Filter

class GetPCUTypes(Method):
    """
    Returns an array of PCU Types.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node']

    accepts = [
        Auth(),
        Mixed([Mixed(PCUType.fields['pcu_type_id'],
                     PCUType.fields['model'])],
               Parameter(str, 'model'),
               Parameter(int, 'node_id'),
               Filter(PCUType.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [PCUType.fields]


    def call(self, auth, pcu_type_filter = None, return_fields = None):

        #Must query at least pcu_type_id
        if return_fields is not None:
            added_fields = []
            if 'pcu_type_id' not in return_fields:
                return_fields.append('pcu_type_id')
                added_fields.append('pcu_type_id')
            if 'pcu_protocol_types' in return_fields and \
               'pcu_protocol_type_ids' not in return_fields:
                return_fields.append('pcu_protocol_type_ids')
                added_fields.append('pcu_protocol_type_ids')
        else:
            added_fields = []

        pcu_types = PCUTypes(self.api, pcu_type_filter, return_fields)

        # remove added fields and protocol_types
        for added_field in added_fields:
            for pcu_type in pcu_types:
                del pcu_type[added_field]

        return pcu_types
