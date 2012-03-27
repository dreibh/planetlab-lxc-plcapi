from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.PCUs import PCU, PCUs
from PLC.Auth import Auth
from PLC.Sites import Site, Sites

can_update = lambda (field, value): field in \
             ['ip', 'hostname', 'protocol',
              'username', 'password',
              'model', 'notes']

class AddPCU(Method):
    """
    Adds a new power control unit (PCU) to the specified site. Any
    fields specified in pcu_fields are used, otherwise defaults are
    used.

    PIs and technical contacts may only add PCUs to their own sites.

    Returns the new pcu_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    pcu_fields = dict(filter(can_update, PCU.fields.items()))

    accepts = [
        Auth(),
        Mixed(Site.fields['site_id'],
              Site.fields['login_base']),
        pcu_fields
        ]

    returns = Parameter(int, 'New pcu_id (> 0) if successful')


    def call(self, auth, site_id_or_login_base, pcu_fields):
        pcu_fields = dict(filter(can_update, pcu_fields.items()))

        # Get associated site details
        sites = Sites(self.api, [site_id_or_login_base])
        if not sites:
            raise PLCInvalidArgument, "No such site"
        site = sites[0]

        if 'admin' not in self.caller['roles']:
            if site['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to add a PCU to that site"

        pcu = PCU(self.api, pcu_fields)
        pcu['site_id'] = site['site_id']
        pcu.sync()

        # Logging variables
        self.event_objects = {'Site': [site['site_id']],
                              'PCU': [pcu['pcu_id']]}
        self.message = 'PCU %d added site %s' % \
                (pcu['pcu_id'], site['site_id'])

        return pcu['pcu_id']
