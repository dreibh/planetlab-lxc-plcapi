from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.PCUs import PCU, PCUs
from PLC.Auth import Auth

class GetPCUs(Method):
    """
    Returns an array of structs containing details about power control
    units (PCUs). If pcu_filter is specified and is an array of PCU
    identifiers, or a struct of PCU attributes, only PCUs matching the
    filter will be returned. If return_fields is specified, only the
    specified details will be returned.

    Admin may query all PCUs. Non-admins may only query the PCUs at
    their sites.
    """

    roles = ['admin', 'pi', 'tech']

    accepts = [
        Auth(),
        Mixed([PCU.fields['pcu_id']],
              Filter(PCU.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [PCU.fields]

    def call(self, auth, pcu_filter = None, return_fields = None):
	# If we are not admin, make sure to only return our own PCUs
        if 'admin' not in self.caller['roles']:
            # Get list of PCUs that we are able to view
            valid_pcu_ids = []
            if self.caller['site_ids']:
                sites = Sites(self.api, self.caller['site_ids'])
                for site in sites:
                    valid_pcu_ids += site['pcu_ids']

            if not valid_pcu_ids:
                return []

            if pcu_filter is None:
                pcu_filter = valid_pcu_ids

        pcus = PCUs(self.api, pcu_filter, return_fields)

        # Filter out PCUs that are not viewable
        if 'admin' not in self.caller['roles']:
            pcus = filter(lambda pcu: pcu['pcu_id'] in valid_pcu_ids, pcus)

        return pcus
