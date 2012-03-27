from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.PCUTypes import PCUType, PCUTypes
from PLC.Auth import Auth

can_update = lambda (field, value): field in \
             ['model', 'name']

class AddPCUType(Method):
    """
    Adds a new pcu type.

    Returns the new pcu_type_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin']

    pcu_type_fields = dict(filter(can_update, PCUType.fields.items()))

    accepts = [
        Auth(),
        pcu_type_fields
        ]

    returns = Parameter(int, 'New pcu_type_id (> 0) if successful')


    def call(self, auth, pcu_type_fields):
        pcu_type_fields = dict(filter(can_update, pcu_type_fields.items()))
        pcu_type = PCUType(self.api, pcu_type_fields)
        pcu_type.sync()
        self.event_object = {'PCUType': [pcu_type['pcu_type_id']]}

        return pcu_type['pcu_type_id']
