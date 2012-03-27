from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.PCUs import PCU, PCUs
from PLC.Auth import Auth

can_update = lambda (field, value): field not in \
             ['pcu_id', 'site_id']

class UpdatePCU(Method):
    """
    Updates the parameters of an existing PCU with the values in
    pcu_fields.

    Non-admins may only update PCUs at their sites.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    update_fields = dict(filter(can_update, PCU.fields.items()))

    accepts = [
        Auth(),
        PCU.fields['pcu_id'],
        update_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, pcu_id, pcu_fields):
        pcu_fields = dict(filter(can_update, pcu_fields.items()))

        # Get associated PCU details
        pcus = PCUs(self.api, [pcu_id])
        if not pcus:
            raise PLCInvalidArgument, "No such PCU"
        pcu = pcus[0]

        if 'admin' not in self.caller['roles']:
            if pcu['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to update that PCU"

        pcu.update(pcu_fields)
        pcu.update_last_updated(commit=False)
        pcu.sync()

        # Logging variables
        self.event_objects = {'PCU': [pcu['pcu_id']]}
        self.message = 'PCU %d updated: %s' % \
                (pcu['pcu_id'], ", ".join(pcu_fields.keys()))
        return 1
