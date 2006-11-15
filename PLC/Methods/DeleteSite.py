from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Sites import Site, Sites
from PLC.Persons import Person, Persons
from PLC.Nodes import Node, Nodes
from PLC.PCUs import PCU, PCUs
from PLC.Auth import Auth

class DeleteSite(Method):
    """
    Mark an existing site as deleted. The accounts of people who are
    not members of at least one other non-deleted site will also be
    marked as deleted. Nodes, PCUs, and slices associated with the
    site will be deleted.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Mixed(Site.fields['site_id'],
              Site.fields['login_base'])
        ]

    returns = Parameter(int, '1 if successful')

    event_type = 'Delete'
    object_type = 'Site'

    def call(self, auth, site_id_or_login_base):
        # Get account information
        sites = Sites(self.api, [site_id_or_login_base])
        if not sites:
            raise PLCInvalidArgument, "No such site"

        site = sites[0]
        site.delete()
	self.object_ids = [site['site_id']]

        return 1
