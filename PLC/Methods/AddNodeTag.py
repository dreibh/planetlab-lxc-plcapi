# $Id$
#
# Thierry Parmentelat - INRIA
#
# $Revision: 9423 $
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.TagTypes import TagType, TagTypes
from PLC.NodeTags import NodeTag, NodeTags
from PLC.Nodes import Node, Nodes

from PLC.Sites import Sites

class AddNodeTag(Method):
    """
    Sets the specified tag for the specified node
    to the specified value.

    In general only tech(s), PI(s) and of course admin(s) are allowed to
    do the change, but this is defined in the node tag type object.

    Returns the new node_tag_id (> 0) if successful, faults
    otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    accepts = [
        Auth(),
        # no other way to refer to a node
        Mixed(Node.fields['node_id'],
              Node.fields['hostname']),
        Mixed(TagType.fields['tag_type_id'],
              TagType.fields['tagname']),
        NodeTag.fields['tagvalue'],
        ]

    returns = Parameter(int, 'New node_tag_id (> 0) if successful')

    object_type = 'Node'


    def call(self, auth, node_id, tag_type_id_or_name, value):
        nodes = Nodes(self.api, [node_id])
        if not nodes:
            raise PLCInvalidArgument, "No such node %r"%node_id
        node = nodes[0]

        tag_types = TagTypes(self.api, [tag_type_id_or_name])
        if not tag_types:
            raise PLCInvalidArgument, "No such node tag type %r"%tag_type_id_or_name
        tag_type = tag_types[0]

	# checks for existence - does not allow several different tags
        conflicts = NodeTags(self.api,
                                        {'node_id':node['node_id'],
                                         'tag_type_id':tag_type['tag_type_id']})

        if len(conflicts) :
            raise PLCInvalidArgument, "Node %d already has tag %d"%(node['node_id'],
                                                                               tag_type['tag_type_id'])

	# check permission : it not admin, is the user affiliated with the right site
	if 'admin' not in self.caller['roles']:
	    # locate node
	    node = Nodes (self.api,[node['node_id']])[0]
	    # locate site
	    site = Sites (self.api, [node['site_id']])[0]
	    # check caller is affiliated with this site
	    if self.caller['person_id'] not in site['person_ids']:
		raise PLCPermissionDenied, "Not a member of the hosting site %s"%site['abbreviated_site']
	    
	    required_min_role = tag_type ['min_role_id']
	    if required_min_role is not None and \
		    min(self.caller['role_ids']) > required_min_role:
		raise PLCPermissionDenied, "Not allowed to modify the specified node tag, requires role %d",required_min_role

        node_tag = NodeTag(self.api)
        node_tag['node_id'] = node['node_id']
        node_tag['tag_type_id'] = tag_type['tag_type_id']
        node_tag['tagvalue'] = value

        node_tag.sync()
	self.object_ids = [node_tag['node_tag_id']]

        return node_tag['node_tag_id']
