from PLC.Faults import *
from PLC.Auth import Auth
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Table import Row
from PLC.Namespace import hostname_to_hrn
from PLC.Peers import Peers
from PLC.Sites import Site, Sites
from PLC.Nodes import Node, Nodes
from PLC.TagTypes import TagTypes
from PLC.NodeTags import NodeTags, NodeTag
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

    accepted_fields = Row.accepted_fields(can_update,Node.fields)
    accepted_fields.update(Node.tags)

    accepts = [
        Auth(),
        Mixed(Site.fields['site_id'],
              Site.fields['login_base']),
        accepted_fields
        ]

    returns = Parameter(int, 'New node_id (> 0) if successful')

    def call(self, auth, site_id_or_login_base, node_fields):

        [native,tags,rejected]=Row.split_fields(node_fields,[Node.fields,Node.tags])

        # type checking
        native = Row.check_fields(native, self.accepted_fields)
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

        # since hostname was specified lets add the 'hrn' node tag
        root_auth = self.api.config.PLC_HRN_ROOT
        login_base = site['login_base']
        tags['hrn'] = hostname_to_hrn(root_auth, login_base, node['hostname'])

        for (tagname,value) in tags.iteritems():
            # the tagtype instance is assumed to exist, just check that
            tag_types = TagTypes(self.api,{'tagname':tagname})
            if not tag_types:
                raise PLCInvalidArgument,"No such TagType %s"%tagname
            tag_type = tag_types[0] 
            node_tags=NodeTags(self.api,{'tagname':tagname,'node_id':node['node_id']})
            if not node_tags:
                node_tag = NodeTag(self.api)
                node_tag['node_id'] = node['node_id']
                node_tag['tag_type_id'] = tag_type['tag_type_id']
                node_tag['tagname']  = tagname
                node_tag['value'] = value
                node_tag.sync()
            else:
                node_tag = node_tags[0]
                node_tag['value'] = value
                node_tag.sync() 

        self.event_objects = {'Site': [site['site_id']],
                              'Node': [node['node_id']]}
        self.message = "Node %d=%s created" % (node['node_id'],node['hostname'])

        return node['node_id']
