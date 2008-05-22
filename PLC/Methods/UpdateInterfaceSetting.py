#
# Thierry Parmentelat - INRIA
#
# $Revision$
#

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.InterfaceSettings import InterfaceSetting, InterfaceSettings
from PLC.Interfaces import Interface, Interfaces

from PLC.Nodes import Nodes
from PLC.Sites import Sites

class UpdateInterfaceSetting(Method):
    """
    Updates the value of an existing interface setting

    Access rights depend on the interface setting type.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    accepts = [
        Auth(),
        InterfaceSetting.fields['interface_setting_id'],
        InterfaceSetting.fields['value']
        ]

    returns = Parameter(int, '1 if successful')

    object_type = 'Interface'

    def call(self, auth, interface_setting_id, value):
        interface_settings = InterfaceSettings(self.api, [interface_setting_id])
        if not interface_settings:
            raise PLCInvalidArgument, "No such interface setting %r"%interface_setting_id
        interface_setting = interface_settings[0]

        ### reproducing a check from UpdateSliceAttribute, looks dumb though
        interfaces = Interfaces(self.api, [interface_setting['interface_id']])
        if not interfaces:
            raise PLCInvalidArgument, "No such interface %r"%interface_setting['interface_id']
        interface = interfaces[0]

        assert interface_setting['interface_setting_id'] in interface['setting_ids']

	# check permission : it not admin, is the user affiliated with the right site
	if 'admin' not in self.caller['roles']:
	    # locate node
	    node = Nodes (self.api,[interface['node_id']])[0]
	    # locate site
	    site = Sites (self.api, [node['site_id']])[0]
	    # check caller is affiliated with this site
	    if self.caller['person_id'] not in site['person_ids']:
		raise PLCPermissionDenied, "Not a member of the hosting site %s"%site['abbreviated_site']
	    
	    required_min_role = interface_setting_type ['min_role_id']
	    if required_min_role is not None and \
		    min(self.caller['role_ids']) > required_min_role:
		raise PLCPermissionDenied, "Not allowed to modify the specified interface setting, requires role %d",required_min_role

        interface_setting['value'] = value
        interface_setting.sync()

	self.object_ids = [interface_setting['interface_setting_id']]
        return 1
