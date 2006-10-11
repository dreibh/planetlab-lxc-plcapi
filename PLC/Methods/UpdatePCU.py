from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.PCUs import PCU, PCUs
from PLC.Auth import PasswordAuth

class UpdatePCU(Method):
    """
    Updates the parameters of an existing PCU with the values in
    pcu_fields.

    Non-admins may only update PCUs at their sites.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    can_update = lambda (field, value): field not in \
                 ['pcu_id', 'site_id']
    update_fields = dict(filter(can_update, PCU.fields.items()))

    accepts = [
        PasswordAuth(),
        PCU.fields['pcu_id'],
        update_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, pcu_id, pcu_fields):
	# Make sure only valid fields are specified
	if filter(lambda field: field not in self.update_fields, pcu_fields):
            raise PLCInvalidArgument, "Invalid field specified"

        # Get associated PCU details
        pcus = PCUs(self.api, [pcu_id]).values()
        if not pcus:
            raise PLCInvalidArgument, "No such PCU"
        pcu = pcus[0]

        if 'admin' not in self.caller['roles']:
            if not pcu_ids:
                ok = False
                sites = Sites(self.api, self.caller['site_ids']).values()
                for site in sites:
                    if pcu['pcu_id'] in site['pcu_ids']:
                        ok = True
                        break
                if not ok:
                    raise PLCPermissionDenied, "Not allowed to update that PCU"

        pcu.update(pcu_fields)
        pcu.sync()

        return 1
