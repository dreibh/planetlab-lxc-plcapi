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

from PLC.Ilinks import Ilink, Ilinks
from PLC.Interfaces import Interface, Interfaces
from PLC.Nodes import Node, Nodes
from PLC.Sites import Site, Sites
from PLC.TagTypes import TagType, TagTypes

class DeleteIlink(Method):
    """
    Deletes the specified ilink

    Attributes may require the caller to have a particular 
    role in order to be deleted, depending on the related tag type.
    Admins may delete attributes of any slice or sliver.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        Ilink.fields['ilink_id']
        ]

    returns = Parameter(int, '1 if successful')

    object_type = 'Interface'


    def call(self, auth, ilink_id):
        ilinks = Ilinks(self.api, [ilink_id])
        if not ilinks:
            raise PLCInvalidArgument, "No such ilink %r"%ilink_id
        ilink = ilinks[0]

        tag_type_id = ilink['tag_type_id']
        tag_type = TagTypes (self.api,[tag_type_id])[0]
        required_min_role = tag_type ['min_role_id']

	# check permission : it not admin, is the user affiliated with the right site<S>
	if 'admin' not in self.caller['roles']:
            for key in ['src_interface_id','dst_interface_id']:
                # locate interface
                interface_id=ilink[key]
                interface = Interfaces (self.api,interface_id)[0]
                node_id=interface['node_id']
                node = Nodes (self.api,node_id) [0]
	        # locate site
                site_id = node['site_id']
                site = Sites (self.api, [site_id]) [0]
	        # check caller is affiliated with this site
                if self.caller['person_id'] not in site['person_ids']:
                    raise PLCPermissionDenied, "Not a member of the hosting site %s"%site['abbreviated_site']
	    
                if required_min_role is not None and \
                        min(self.caller['role_ids']) > required_min_role:
                    raise PLCPermissionDenied, "Not allowed to modify the specified ilink, requires role %d",required_min_role

        ilink.delete()
	self.object_ids = [ilink['src_interface_id'],ilink['dst_interface_id']]

        return 1
