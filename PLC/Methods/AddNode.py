from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.Sites import Site, Sites
from PLC.Auth import Auth

can_update = lambda (field, value): field in \
             ['hostname', 'boot_state', 'model', 'version']

class AddNode(Method):
    """
    Adds a new node. Any values specified in node_fields are used,
    otherwise defaults are used.

    PIs and techs may only add nodes to their own sites. Admins may
    add nodes to any site.

    Returns the new node_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    node_fields = dict(filter(can_update, Node.fields.items()))

    accepts = [
        Auth(),
        Mixed(Site.fields['site_id'],
              Site.fields['login_base']),
        node_fields
        ]

    returns = Parameter(int, 'New node_id (> 0) if successful')

    event_type = 'Add'
    object_type = 'Node'

    def call(self, auth, site_id_or_login_base, node_fields):
        node_fields = dict(filter(can_update, node_fields.items()))

        # Get site information
        sites = Sites(self.api, [site_id_or_login_base])
        if not sites:
            raise PLCInvalidArgument, "No such site"

        site = sites[0]

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

        node = Node(self.api, node_fields)
        node['site_id'] = site['site_id']
        # xxx temporary, until I figure a way to get local/foreign nodes
        # so far I cannot seem to use a filter/dict like {'~peer_id':None}
        # node['peer_id'] = 0
        node.sync()

	self.object_ids = [site['site_id'], node['node_id']]	

        return node['node_id']
