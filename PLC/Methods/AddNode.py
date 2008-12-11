# $Id$
from PLC.Faults import *
from PLC.Auth import Auth
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Table import Row

from PLC.Sites import Site, Sites
from PLC.Nodes import Node, Nodes
from PLC.TagTypes import TagTypes
from PLC.NodeTags import NodeTags
from PLC.Methods.AddNodeTag import AddNodeTag
from PLC.Methods.UpdateNodeTag import UpdateNodeTag

can_update = ['hostname', 'node_type', 'boot_state', 'model', 'version']

class AddNode(Method):
    """
    Adds a new node. Any values specified in node_fields are used,
    otherwise defaults are used.

    PIs and techs may only add nodes to their own sites. Admins may
    add nodes to any site.

    Returns the new node_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    accepted_fields = Row.accepted_fields(can_update, [Node.fields,Node.tags])

    accepts = [
        Auth(),
        Mixed(Site.fields['site_id'],
              Site.fields['login_base']),
        accepted_fields
        ]

    returns = Parameter(int, 'New node_id (> 0) if successful')

    def call(self, auth, site_id_or_login_base, node_fields):

        [native,tags,rejected]=Row.split_fields(node_fields,[Node.fields,Node.tags])

        if rejected:
            raise PLCInvalidArgument, "Cannot add Node with column(s) %r"%rejected

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

        node = Node(self.api, native)
        node['site_id'] = site['site_id']
        node.sync()

        for (tagname,value) in tags.iteritems():
            # the tagtype instance is assumed to exist, just check that
            if not TagTypes(self.api,{'tagname':tagname}):
                raise PLCInvalidArgument,"No such TagType %s"%tagname
            node_tags=NodeTags(self.api,{'tagname':tagname,'node_id':node['node_id']})
            if not node_tags:
                AddNodeTag(self.api).__call__(auth,node['node_id'],tagname,value)
            else:
                UpdateNodeTag(self.api).__call__(auth,node_tags[0]['node_tag_id'],value)

	self.event_objects = {'Site': [site['site_id']],
			     'Node': [node['node_id']]}	
	self.message = "Node %s created" % node['node_id']

        return node['node_id']
