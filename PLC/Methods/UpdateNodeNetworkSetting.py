#
# Thierry Parmentelat - INRIA
#
# $Revision: 90 $
#

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.NodeNetworkSettings import NodeNetworkSetting, NodeNetworkSettings
from PLC.NodeNetworks import NodeNetwork, NodeNetworks

from PLC.Nodes import Nodes
from PLC.Sites import Sites

class UpdateNodeNetworkSetting(Method):
    """
    Updates the value of an existing nodenetwork setting

    Access rights depend on the nodenetwork setting type.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    accepts = [
        Auth(),
        NodeNetworkSetting.fields['nodenetwork_setting_id'],
        NodeNetworkSetting.fields['value']
        ]

    returns = Parameter(int, '1 if successful')

    object_type = 'NodeNetwork'

    def call(self, auth, nodenetwork_setting_id, value):
        nodenetwork_settings = NodeNetworkSettings(self.api, [nodenetwork_setting_id])
        if not nodenetwork_settings:
            raise PLCInvalidArgument, "No such nodenetwork setting %r"%nodenetwork_setting_id
        nodenetwork_setting = nodenetwork_settings[0]

        ### reproducing a check from UpdateSliceAttribute, looks dumb though
        nodenetworks = NodeNetworks(self.api, [nodenetwork_setting['nodenetwork_id']])
        if not nodenetworks:
            raise PLCInvalidArgument, "No such nodenetwork %r"%nodenetwork_setting['nodenetwork_id']
        nodenetwork = nodenetworks[0]

        assert nodenetwork_setting['nodenetwork_setting_id'] in nodenetwork['nodenetwork_setting_ids']

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

        nodenetwork_setting['value'] = value
        nodenetwork_setting.sync()

	self.object_ids = [nodenetwork_setting['nodenetwork_setting_id']]
        return 1