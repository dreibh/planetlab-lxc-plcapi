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

from PLC.Sites import Sites

class UpdateIlink(Method):
    """
    Updates the value of an existing ilink

    Access rights depend on the tag type.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    accepts = [
        Auth(),
        Ilink.fields['ilink_id'],
        Ilink.fields['value']
        ]

    returns = Parameter(int, '1 if successful')

    object_type = 'Interface'

    def call(self, auth, ilink_id, value):
        ilinks = Ilinks(self.api, [ilink_id])
        if not ilinks:
            raise PLCInvalidArgument, "No such ilink %r"%ilink_id
        ilink = ilinks[0]

	if 'admin' not in self.caller['roles']:
#	# check permission : it not admin, is the user affiliated with the right site
#	    # locate node
#	    node = Nodes (self.api,[node['node_id']])[0]
#	    # locate site
#	    site = Sites (self.api, [node['site_id']])[0]
#	    # check caller is affiliated with this site
#	    if self.caller['person_id'] not in site['person_ids']:
#		raise PLCPermissionDenied, "Not a member of the hosting site %s"%site['abbreviated_site']
	    
	    required_min_role = tag_type ['min_role_id']
	    if required_min_role is not None and \
		    min(self.caller['role_ids']) > required_min_role:
		raise PLCPermissionDenied, "Not allowed to modify the specified ilink, requires role %d",required_min_role

        ilink['value'] = value
        ilink.sync()

	self.object_ids = [ilink['src_interface_id'],ilink['dst_interface_id']]
        return 1
