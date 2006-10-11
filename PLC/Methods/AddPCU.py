from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.PCUs import PCU, PCUs
from PLC.Auth import PasswordAuth
from PLC.Sites import Site, Sites

class AddPCU(Method):
    """
    Adds a new power control unit (PCU) to the specified site. Any
    fields specified in optional_vals are used, otherwise defaults are
    used.

    PIs and technical contacts may only add PCUs to their own sites.

    Returns the new pcu_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    can_update = lambda (field, value): field in \
                 ['hostname', 'ip', 'protocol',
                  'username', 'password',
                  'model', 'notes']
    update_fields = dict(filter(can_update, PCU.fields.items()))

    accepts = [
        PasswordAuth(),
        Mixed(Site.fields['site_id'],
              Site.fields['login_base']),
        update_fields
        ]

    returns = Parameter(int, 'New pcu_id (> 0) if successful')

    def call(self, auth, site_id_or_login_base, optional_vals = {}):
        if filter(lambda field: field not in self.update_fields, optional_vals):
            raise PLCInvalidArgument, "Invalid field specified"

        # Get associated site details
        sites = Sites(self.api, [site_id_or_login_base]).values()
        if not sites:
            raise PLCInvalidArgument, "No such site"
        site = sites[0]

        if 'admin' not in self.caller['roles']:
            if site['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to add a PCU to that site"

        pcu = PCU(self.api, optional_vals)
        pcu['site_id'] = site['site_id']
        pcu.sync()

        return pcu['pcu_id']
