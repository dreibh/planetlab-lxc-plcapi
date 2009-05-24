# $Id: $
from PLC.v42Legacy import patch
from PLC.v42LegacyNodeNetworkSettings import v42rename, v43rename
from PLC.Methods.UpdateInterfaceTag import UpdateInterfaceTag
class UpdateNodeNetworkSetting(UpdateInterfaceTag):
    """ Legacy version of UpdateInterfaceTag. """
    skip_typecheck = True
    status = "deprecated"
    def call(self, auth, interface_tag_id, value):
	interface_tag_id=patch(interface_tag_id,v42rename)
	value=patch(value,v42rename)
	result=UpdateInterfaceTag.call(self,auth,interface_tag_id,value)
	return patch(result,v43rename)
