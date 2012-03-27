from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Sites import Site, Sites
from PLC.Persons import Person, Persons
from PLC.Nodes import Node, Nodes
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

    roles = ['admin', 'pi', 'tech', 'node']

    accepts = [
        Auth(),
        Mixed([PCU.fields['pcu_id']],
              Filter(PCU.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [PCU.fields]

    def call(self, auth, pcu_filter = None, return_fields = None):
        # If we are not admin
        if not (isinstance(self.caller, Person) and 'admin' in self.caller['roles']):
            # Return only the PCUs at our site
            valid_pcu_ids = []

            if isinstance(self.caller, Person):
                site_ids = self.caller['site_ids']
            elif isinstance(self.caller, Node):
                site_ids = [self.caller['site_id']]

            for site in Sites(self.api, site_ids):
                valid_pcu_ids += site['pcu_ids']

            if not valid_pcu_ids:
                return []

            if pcu_filter is None:
                pcu_filter = valid_pcu_ids

        # Must query at least slice_id (see below)
        if return_fields is not None and 'pcu_id' not in return_fields:
            return_fields.append('pcu_id')
            added_fields = True
        else:
            added_fields = False

        pcus = PCUs(self.api, pcu_filter, return_fields)

        # Filter out PCUs that are not viewable
        if not (isinstance(self.caller, Person) and 'admin' in self.caller['roles']):
            pcus = filter(lambda pcu: pcu['pcu_id'] in valid_pcu_ids, pcus)

        # Remove pcu_id if not specified
        if added_fields:
            for pcu in pcus:
                if 'pcu_id' in pcu:
                    del pcu['pcu_id']

        return pcus
