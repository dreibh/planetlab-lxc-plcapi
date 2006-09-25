from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.Sites import Site, Sites
from PLC.Auth import PasswordAuth

class AdmAddNode(Method):
    """
    Adds a new node. Any values specified in optional_vals are used,
    otherwise defaults are used.

    PIs and techs may only add nodes to their own sites. Admins may
    add nodes to any site.

    Returns the new node_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    can_update = lambda (field, value): field in \
                 ['model', 'version']
    update_fields = dict(filter(can_update, Node.fields.items()))

    accepts = [
        PasswordAuth(),
        Mixed(Site.fields['site_id'],
              Site.fields['login_base']),
        Node.fields['hostname'],
        Node.fields['boot_state'],
        update_fields
        ]

    returns = Parameter(int, 'New node_id (> 0) if successful')

    def call(self, auth, site_id_or_login_base, hostname, boot_state, optional_vals = {}):
        if filter(lambda field: field not in self.update_fields, optional_vals):
            raise PLCInvalidArgument, "Invalid fields specified"

        # Get site information
        sites = Sites(self.api, [site_id_or_login_base])
        if not sites:
            raise PLCInvalidArgument, "No such site"

        site = sites.values()[0]

        # Authenticated function
        assert self.caller is not None

        # If we are not an admin, make sure that the caller is a
        # member of the site.
        if 'admin' not in self.caller['roles']:
            if site['site_id'] not in self.caller['site_ids']:
                assert self.caller['person_id'] not in site['person_ids']
                raise PLCPermissionDenied, "Not allowed to add nodes to specified site"
            else:
                assert self.caller['person_id'] in site['person_ids']

        node = Node(self.api, optional_vals)
        node['hostname'] = hostname
        node['boot_state'] = boot_state
        node['site_id'] = site['site_id']
        node.sync(commit = False)

        return node['node_id']
