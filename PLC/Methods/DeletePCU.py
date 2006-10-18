from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.PCUs import PCU, PCUs
from PLC.Auth import PasswordAuth

class DeletePCU(Method):
    """
    Deletes a PCU.

    Non-admins may only delete PCUs at their sites.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    accepts = [
        PasswordAuth(),
        PCU.fields['pcu_id'],
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, pcu_id):
        # Get associated PCU details
        pcus = PCUs(self.api, [pcu_id]).values()
        if not pcus:
            raise PLCInvalidArgument, "No such PCU"
        pcu = pcus[0]

        if 'admin' not in self.caller['roles']:
            if pcu['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to update that PCU"

        pcu.delete()

        return 1
