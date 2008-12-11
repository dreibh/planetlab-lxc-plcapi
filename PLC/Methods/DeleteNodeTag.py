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

from PLC.NodeTags import NodeTag, NodeTags
from PLC.Nodes import Node, Nodes

from PLC.Nodes import Node, Nodes
from PLC.Sites import Site, Sites

class DeleteNodeTag(Method):
    """
    Deletes the specified node tag

    Attributes may require the caller to have a particular role in order
    to be deleted, depending on the related node tag type.
    Admins may delete attributes of any slice or sliver.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        NodeTag.fields['node_tag_id']
        ]

    returns = Parameter(int, '1 if successful')

    object_type = 'Node'


    def call(self, auth, node_tag_id):
        node_tags = NodeTags(self.api, [node_tag_id])
        if not node_tags:
            raise PLCInvalidArgument, "No such node tag %r"%node_tag_id
        node_tag = node_tags[0]

        ### reproducing a check from UpdateSliceTag, looks dumb though
        nodes = Nodes(self.api, [node_tag['node_id']])
        if not nodes:
            raise PLCInvalidArgument, "No such node %r"%node_tag['node_id']
        node = nodes[0]

        assert node_tag['node_tag_id'] in node['node_tag_ids']

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

        node_tag.delete()
	self.object_ids = [node_tag['node_tag_id']]

        return 1
