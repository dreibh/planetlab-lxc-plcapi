#
# Thierry Parmentelat - INRIA
#
# $Revision: 9423 $
#

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.Ilinks import Ilink, Ilinks
from PLC.Nodes import Node, Nodes

from PLC.Nodes import Node, Nodes
from PLC.Sites import Site, Sites

class DeleteIlink(Method):
    """
    Deletes the specified ilink

    Attributes may require the caller to have a particular role in order
    to be deleted, depending on the related ilink type.
    Admins may delete attributes of any slice or sliver.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        Ilink.fields['ilink_id']
        ]

    returns = Parameter(int, '1 if successful')

    object_type = 'Node'


    def call(self, auth, ilink_id):
        ilinks = Ilinks(self.api, [ilink_id])
        if not ilinks:
            raise PLCInvalidArgument, "No such ilink %r"%ilink_id
        ilink = ilinks[0]

        ### reproducing a check from UpdateSliceAttribute, looks dumb though
        nodes = Nodes(self.api, [ilink['node_id']])
        if not nodes:
            raise PLCInvalidArgument, "No such node %r"%ilink['node_id']
        node = nodes[0]

        assert ilink['ilink_id'] in node['tag_ids']

	# check permission : it not admin, is the user affiliated with the right site
	if 'admin' not in self.caller['roles']:
	    # locate node
	    node = Nodes (self.api,[node['node_id']])[0]
	    # locate site
	    site = Sites (self.api, [node['site_id']])[0]
	    # check caller is affiliated with this site
	    if self.caller['person_id'] not in site['person_ids']:
		raise PLCPermissionDenied, "Not a member of the hosting site %s"%site['abbreviated_site']
	    
	    required_min_role = ilink_type ['min_role_id']
	    if required_min_role is not None and \
		    min(self.caller['role_ids']) > required_min_role:
		raise PLCPermissionDenied, "Not allowed to modify the specified ilink, requires role %d",required_min_role

        ilink.delete()
	self.object_ids = [ilink['ilink_id']]

        return 1
