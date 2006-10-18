from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.PCUs import PCU, PCUs
from PLC.Sites import Site, Sites
from PLC.Auth import PasswordAuth

class AdmGetSitePowerControlUnits(Method):
    """
    Deprecated. Functionality can be implemented with GetSites and GetPCUs.
    """

    status = "deprecated"

    roles = ['admin', 'pi', 'tech']

    accepts = [
        PasswordAuth(),
        Mixed(Site.fields['site_id'],
              Site.fields['login_base'])
        ]

    returns = [PCU.fields]

    def call(self, auth, site_id_or_login_base):
        sites = Sites(self.api, [site_id_or_login_base])
        if not sites:
            raise PLCInvalidArgument, "No such site"
        site = sites.values()[0]

        if 'admin' not in self.caller['roles']:
            if site['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to view the PCUs at that site"

        pcus = PCUs(self.api, site['pcu_ids']).values()

	# turn each pcu into a real dict
	pcus = [dict(pcu) for pcu in pcus]

        return pcus