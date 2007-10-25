#
# Thierry Parmentelat - INRIA
#
# $Revision$
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.NodeNetworkSettingTypes import NodeNetworkSettingType, NodeNetworkSettingTypes
from PLC.NodeNetworkSettings import NodeNetworkSetting, NodeNetworkSettings
from PLC.NodeNetworks import NodeNetwork, NodeNetworks

from PLC.Nodes import Nodes
from PLC.Sites import Sites

class AddNodeNetworkSetting(Method):
    """
    Sets the specified setting for the specified nodenetwork
    to the specified value.

    In general only tech(s), PI(s) and of course admin(s) are allowed to
    do the change, but this is defined in the nodenetwork setting type object.

    Returns the new nodenetwork_setting_id (> 0) if successful, faults
    otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    accepts = [
        Auth(),
        # no other way to refer to a nodenetwork
        NodeNetworkSetting.fields['nodenetwork_id'],
        Mixed(NodeNetworkSettingType.fields['nodenetwork_setting_type_id'],
              NodeNetworkSettingType.fields['name']),
        NodeNetworkSetting.fields['value'],
        ]

    returns = Parameter(int, 'New nodenetwork_setting_id (> 0) if successful')

    object_type = 'NodeNetwork'


    def call(self, auth, nodenetwork_id, nodenetwork_setting_type_id_or_name, value):
        nodenetworks = NodeNetworks(self.api, [nodenetwork_id])
        if not nodenetworks:
            raise PLCInvalidArgument, "No such nodenetwork %r"%nodenetwork_id
        nodenetwork = nodenetworks[0]

        nodenetwork_setting_types = NodeNetworkSettingTypes(self.api, [nodenetwork_setting_type_id_or_name])
        if not nodenetwork_setting_types:
            raise PLCInvalidArgument, "No such nodenetwork setting type %r"%nodenetwork_setting_type_id_or_name
        nodenetwork_setting_type = nodenetwork_setting_types[0]

	# checks for existence - does not allow several different settings
        conflicts = NodeNetworkSettings(self.api,
                                        {'nodenetwork_id':nodenetwork['nodenetwork_id'],
                                         'nodenetwork_setting_type_id':nodenetwork_setting_type['nodenetwork_setting_type_id']})

        if len(conflicts) :
            raise PLCInvalidArgument, "Nodenetwork %d already has setting %d"%(nodenetwork['nodenetwork_id'],
                                                                               nodenetwork_setting_type['nodenetwork_setting_type_id'])

	# check permission : it not admin, is the user affiliated with the right site
	if 'admin' not in self.caller['roles']:
	    # locate node
	    node = Nodes (self.api,[nodenetwork['node_id']])[0]
	    # locate site
	    site = Sites (self.api, [node['site_id']])[0]
	    # check caller is affiliated with this site
	    if self.caller['person_id'] not in site['person_ids']:
		raise PLCPermissionDenied, "Not a member of the hosting site %s"%site['abbreviated_site']
	    
	    required_min_role = nodenetwork_setting_type ['min_role_id']
	    if required_min_role is not None and \
		    min(self.caller['role_ids']) > required_min_role:
		raise PLCPermissionDenied, "Not allowed to modify the specified nodenetwork setting, requires role %d",required_min_role

        nodenetwork_setting = NodeNetworkSetting(self.api)
        nodenetwork_setting['nodenetwork_id'] = nodenetwork['nodenetwork_id']
        nodenetwork_setting['nodenetwork_setting_type_id'] = nodenetwork_setting_type['nodenetwork_setting_type_id']
        nodenetwork_setting['value'] = value

        nodenetwork_setting.sync()
	self.object_ids = [nodenetwork_setting['nodenetwork_setting_id']]

        return nodenetwork_setting['nodenetwork_setting_id']
