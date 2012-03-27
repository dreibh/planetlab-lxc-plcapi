from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.PCUTypes import PCUType, PCUTypes
from PLC.Auth import Auth

can_update = lambda (field, value): field in \
             ['model', 'name']

class UpdatePCUType(Method):
    """
    Updates a PCU type. Only the fields specified in
    pcu_typee_fields are updated, all other fields are left untouched.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    pcu_type_fields = dict(filter(can_update, PCUType.fields.items()))

    accepts = [
        Auth(),
        PCUType.fields['pcu_type_id'],
        pcu_type_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, pcu_type_id, pcu_type_fields):
        pcu_type_fields = dict(filter(can_update, pcu_type_fields.items()))

        pcu_types = PCUTypes(self.api, [pcu_type_id])
        if not pcu_types:
            raise PLCInvalidArgument, "No such pcu type"

        pcu_type = pcu_types[0]
        pcu_type.update(pcu_type_fields)
        pcu_type.sync()
        self.event_objects = {'PCUType': [pcu_type['pcu_type_id']]}

        return 1
