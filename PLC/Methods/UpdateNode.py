# $Id$
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Table import Row
from PLC.Auth import Auth

from PLC.Nodes import Node, Nodes
from PLC.TagTypes import TagTypes
from PLC.NodeTags import NodeTags
from PLC.Methods.AddNodeTag import AddNodeTag
from PLC.Methods.UpdateNodeTag import UpdateNodeTag

can_update = ['hostname', 'boot_state', 'model', 'version','key', 'session', 'boot_nonce', 'site_id'] + \
              Node.related_fields.keys()

class UpdateNode(Method):
    """
    Updates a node. Only the fields specified in node_fields are
    updated, all other fields are left untouched.
    
    PIs and techs can update only the nodes at their sites. Only
    admins can update the key, session, and boot_nonce fields.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech']

    node_fields = Row.accepted_fields(can_update,[Node.fields,Node.related_fields,Node.tags])

    accepts = [
        Auth(),
        Mixed(Node.fields['node_id'],
              Node.fields['hostname']),
        node_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, node_id_or_hostname, node_fields):
        
        node_fields = Row.check_fields (node_fields, self.accepted_fields)

        # split provided fields 
        [native,related,tags,rejected] = Row.split_fields(node_fields,[Node.fields,Node.related_fields,Node.tags])

        if rejected:
            raise PLCInvalidArgument, "Cannot update Node column(s) %r"%rejected

	# Remove admin only fields
	if 'admin' not in self.caller['roles']:
            for key in 'key', 'session', 'boot_nonce', 'site_id':
                if native.has_key(key):
                    del native[key]

        # Get account information
        nodes = Nodes(self.api, [node_id_or_hostname])
        if not nodes:
            raise PLCInvalidArgument, "No such node %r"%node_id_or_hostname
        node = nodes[0]

        if node['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local node %r"%node_id_or_hostname

        # Authenticated function
        assert self.caller is not None

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
	
        for (tagname,value) in tags.iteritems():
            # the tagtype instance is assumed to exist, just check that
            if not TagTypes(self.api,{'tagname':tagname}):
                raise PLCInvalidArgument,"No such TagType %s"%tagname
            node_tags=NodeTags(self.api,{'tagname':tagname,'node_id':node['node_id']})
            if not node_tags:
                AddNodeTag(self.api).__call__(auth,node['node_id'],tagname,value)
            else:
                UpdateNodeTag(self.api).__call__(auth,node_tags[0]['node_tag_id'],value)

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
