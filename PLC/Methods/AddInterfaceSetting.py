#
# Thierry Parmentelat - INRIA
#
# $Revision$
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.TagTypes import TagType, TagTypes
from PLC.InterfaceSettings import InterfaceSetting, InterfaceSettings
from PLC.Interfaces import Interface, Interfaces

from PLC.Nodes import Nodes
from PLC.Sites import Sites

class AddInterfaceSetting(Method):
    """
    Sets the specified setting for the specified interface
    to the specified value.

    In general only tech(s), PI(s) and of course admin(s) are allowed to
    do the change, but this is defined in the tag type object.

    Returns the new interface_setting_id (> 0) if successful, faults
    otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    accepts = [
        Auth(),
        # no other way to refer to a interface
        InterfaceSetting.fields['interface_id'],
        Mixed(TagType.fields['tag_type_id'],
              TagType.fields['tagname']),
        InterfaceSetting.fields['value'],
        ]

    returns = Parameter(int, 'New interface_setting_id (> 0) if successful')

    object_type = 'Interface'


    def call(self, auth, interface_id, tag_type_id_or_name, value):
        interfaces = Interfaces(self.api, [interface_id])
        if not interfaces:
            raise PLCInvalidArgument, "No such interface %r"%interface_id
        interface = interfaces[0]

        tag_types = TagTypes(self.api, [tag_type_id_or_name])
        if not tag_types:
            raise PLCInvalidArgument, "No such tag type %r"%tag_type_id_or_name
        tag_type = tag_types[0]

	# checks for existence - does not allow several different settings
        conflicts = InterfaceSettings(self.api,
                                        {'interface_id':interface['interface_id'],
                                         'tag_type_id':tag_type['tag_type_id']})

        if len(conflicts) :
            raise PLCInvalidArgument, "Interface %d already has setting %d"%(interface['interface_id'],
                                                                               tag_type['tag_type_id'])

	# check permission : it not admin, is the user affiliated with the right site
	if 'admin' not in self.caller['roles']:
	    # locate node
	    node = Nodes (self.api,[interface['node_id']])[0]
	    # locate site
	    site = Sites (self.api, [node['site_id']])[0]
	    # check caller is affiliated with this site
	    if self.caller['person_id'] not in site['person_ids']:
		raise PLCPermissionDenied, "Not a member of the hosting site %s"%site['abbreviated_site']
	    
	    required_min_role = tag_type ['min_role_id']
	    if required_min_role is not None and \
		    min(self.caller['role_ids']) > required_min_role:
		raise PLCPermissionDenied, "Not allowed to modify the specified interface setting, requires role %d",required_min_role

        interface_setting = InterfaceSetting(self.api)
        interface_setting['interface_id'] = interface['interface_id']
        interface_setting['tag_type_id'] = tag_type['tag_type_id']
        interface_setting['value'] = value

        interface_setting.sync()
	self.object_ids = [interface_setting['interface_setting_id']]

        return interface_setting['interface_setting_id']
