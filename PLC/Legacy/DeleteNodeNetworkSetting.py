# $Id: $
from PLC.v42Legacy import patch
from PLC.v42LegacyNodeNetworkSettings import v42rename, v43rename
from PLC.Methods.DeleteInterfaceTag import DeleteInterfaceTag
class DeleteNodeNetworkSetting(DeleteInterfaceTag):
    """ Legacy version of DeleteInterfaceTag. """
    status = "deprecated"
    def call(self, auth, interface_tag_id):
	interface_tag_id=patch(interface_tag_id,v42rename)
	result=DeleteInterfaceTag.call(self,auth,interface_tag_id)
	return patch(result,v43rename)
