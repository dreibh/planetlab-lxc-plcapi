from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Sites import Site, Sites
from PLC.Persons import Person, Persons
from PLC.Nodes import Node, Nodes
from PLC.PCUs import PCU, PCUs
from PLC.Auth import PasswordAuth

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
        PasswordAuth(),
        Mixed(Site.fields['site_id'],
              Site.fields['login_base'])
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, site_id_or_login_base):
        # Get account information
        sites = Sites(self.api, [site_id_or_login_base])
        if not sites:
            raise PLCInvalidArgument, "No such site"

        site = sites.values()[0]
        site.delete()

        return 1
