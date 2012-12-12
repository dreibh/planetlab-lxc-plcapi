from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Table import Row
from PLC.Auth import Auth
from PLC.Namespace import hostname_to_hrn
from PLC.Peers import Peers
from PLC.Sites import Sites
from PLC.Nodes import Node, Nodes
from PLC.TagTypes import TagTypes
from PLC.NodeTags import NodeTags, NodeTag

admin_only = [ 'key', 'session', 'boot_nonce', 'site_id']
can_update = ['hostname', 'node_type', 'boot_state', 'model', 'version'] + admin_only

class UpdateNode(Method):
    """
    Updates a node. Only the fields specified in node_fields are
    updated, all other fields are left untouched.

    PIs and techs can update only the nodes at their sites. Only
    admins can update the key, session, and boot_nonce fields.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    accepted_fields = Row.accepted_fields(can_update,Node.fields)
    # xxx check the related_fields feature
    accepted_fields.update(Node.related_fields)
    accepted_fields.update(Node.tags)

    accepts = [
        Auth(),
        Mixed(Node.fields['node_id'],
              Node.fields['hostname']),
        accepted_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, node_id_or_hostname, node_fields):

        # split provided fields
        [native,related,tags,rejected] = Row.split_fields(node_fields,[Node.fields,Node.related_fields,Node.tags])

        # type checking
        native = Row.check_fields (native, self.accepted_fields)
        if rejected:
            raise PLCInvalidArgument, "Cannot update Node column(s) %r"%rejected

        # Authenticated function
        assert self.caller is not None

        # Remove admin only fields
        if 'admin' not in self.caller['roles']:
            for key in admin_only:
                if native.has_key(key):
                    del native[key]

        # Get account information
        nodes = Nodes(self.api, [node_id_or_hostname])
        if not nodes:
            raise PLCInvalidArgument, "No such node %r"%node_id_or_hostname
        node = nodes[0]

        if node['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local node %r"%node_id_or_hostname

        # If we are not an admin, make sure that the caller is a
        # member of the site at which the node is located.
        if 'admin' not in self.caller['roles']:
            if node['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Not allowed to delete nodes from specified site"

        # Make requested associations
        for (k,v) in related.iteritems():
            node.associate(auth, k,v)

        node.update(native)
        node.update_last_updated(commit=False)
        node.sync(commit=True)

        # if hostname was modifed make sure to update the hrn
        # tag
        if 'hostname' in native:
            root_auth = self.api.config.PLC_HRN_ROOT
            # sub auth is the login base of this node's site
            sites = Sites(self.api, node['site_id'], ['login_base'])
            site = sites[0]
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

        # Logging variables
        self.event_objects = {'Node': [node['node_id']]}
        if 'hostname' in node:
            self.message = 'Node %s updated'%node['hostname']
        else:
            self.message = 'Node %d updated'%node['node_id']
        self.message += " [%s]." % (", ".join(node_fields.keys()),)
        if 'boot_state' in node_fields.keys():
            self.message += ' boot_state updated to %s' % node_fields['boot_state']

        return 1
