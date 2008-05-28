#
# Thierry Parmentelat - INRIA
#
# $Revision: 9423 $
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.LinkTypes import LinkType, LinkTypes
from PLC.Ilinks import Ilink, Ilinks
from PLC.Interfaces import Interface, Interfaces

from PLC.Sites import Sites

class AddIlink(Method):
    """
    Create a link between two interfaces
    The link has a type, that needs be created beforehand
    and an optional value. 

    Returns the new ilink_id (> 0) if successful, faults
    otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    accepts = [
        Auth(),
        # refer to either the id or the type name
        Ilink.fields['src_interface_id'],
        Ilink.fields['dst_interface_id'],
        Mixed(LinkType.fields['link_type_id'],
              LinkType.fields['name']),
        Ilink.fields['value'],
        ]

    returns = Parameter(int, 'New ilink_id (> 0) if successful')

    def call(self, auth,  src_if_id, dst_if_id, link_type_id_or_name, value):

        src_if = Interfaces (self.api, [src_if_id],[interface_id])
        if not src_if:
            raise PLCInvalidArgument, "No such source interface %r"%src_if_id
        dst_if = Interfaces (self.api, [dst_if_id],[interface_id])
        if not dst_if:
            raise PLCInvalidArgument, "No such destination interface %r"%dst_if_id

        link_types = LinkTypes(self.api, [link_type_id_or_name])
        if not link_types:
            raise PLCInvalidArgument, "No such ilink type %r"%link_type_id_or_name
        link_type = link_types[0]

	# checks for existence - with the same type
        conflicts = Ilinks(self.api,
                           {'link_type_id':link_type['link_type_id'],
                            'src_interface_id':src_if_id,
                            'dst_interface_id':dst_if_id,})

        if len(conflicts) :
            ilink=conflicts[0]
            raise PLCInvalidArgument, "Ilink (%s,%d,%d) already exists and has value %r"\
                %(link_type['name'],src_if_id,dst_if_id,ilink['value'])

	if 'admin' not in self.caller['roles']:
#	# check permission : it not admin, is the user affiliated with the right site(s) ????
#	    # locate node
#	    node = Nodes (self.api,[node['node_id']])[0]
#	    # locate site
#	    site = Sites (self.api, [node['site_id']])[0]
#	    # check caller is affiliated with this site
#	    if self.caller['person_id'] not in site['person_ids']:
#		raise PLCPermissionDenied, "Not a member of the hosting site %s"%site['abbreviated_site']
	    
	    required_min_role = link_type ['min_role_id']
	    if required_min_role is not None and \
		    min(self.caller['role_ids']) > required_min_role:
		raise PLCPermissionDenied, "Not allowed to modify the specified ilink, requires role %d",required_min_role

        ilink = Ilink(self.api)
        ilink['link_type_id'] = link_type['link_type_id']
        ilink['src_interface_id'] = src_if_id
        ilink['dst_interface_id'] = dst_if_id
        ilink['value'] = value

        ilink.sync()

        self.object_type = 'Interface'
	self.object_ids = [src_if_id,dst_if_id]

        return ilink['ilink_id']
