from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.Sites import Site, Sites
from PLC.Auth import PasswordAuth

can_update = lambda (field, value): field in \
             ['hostname', 'site_id', 'boot_state', 'model', 'version']

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
        PasswordAuth(),
        node_fields
        ]

    returns = Parameter(int, 'New node_id (> 0) if successful')

    event_type = 'Add'
    object_type = 'Node'
    object_ids = []

    def call(self, auth, node_fields = {}):
        node_fields = dict(filter(can_update, node_fields.items()))
        
        # Get site information
        sites = Sites(self.api, [node_fields['site_id']])
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

        node = Node(self.api, node_fields)
        node.sync()

	self.object_ids = [site['site_id'], node['node_id']]	

        return node['node_id']
