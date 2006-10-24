from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.PCUs import PCU, PCUs
from PLC.Auth import PasswordAuth

class GetPCUs(Method):
    """
    Return an array of structs containing details about PCUs. If
    pcu_id_list is specified, only the specified PCUs will be queried.

    Admin may query all PCUs. Non-admins may only query the PCUs at
    their sites.
    """

    roles = ['admin', 'pi', 'tech']

    accepts = [
        PasswordAuth(),
        [PCU.fields['pcu_id']]
        ]

    returns = [PCU.fields]

    def call(self, auth, pcu_ids = None):
	# If we are not admin, make sure to only return our own PCUs
        if 'admin' not in self.caller['roles']:
            # Get list of PCUs that we are able to view
            valid_pcu_ids = []
            if self.caller['site_ids']:
                sites = Sites(self.api, self.caller['site_ids']).values()
                for site in sites:
                    valid_pcu_ids += site['pcu_ids']

            pcu_ids = set(pcu_ids).intersection(valid_pcu_ids)
            if not pcu_ids:
                return []

        return PCUs(self.api, pcu_ids).values()
