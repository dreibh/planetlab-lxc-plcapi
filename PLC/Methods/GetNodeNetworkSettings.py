# $Id: $
from PLC.v42Legacy import patch
from PLC.v42LegacyNodeNetworkSettings import v42rename, v43rename
from PLC.Methods.GetInterfaceTags import GetInterfaceTags
class GetNodeNetworkSettings(GetInterfaceTags):
    """ Legacy version of GetInterfaceTags. """
    status = "deprecated"
    def call(self, auth, interface_tag_filter = None, return_fields = None):
	interface_tag_filter=patch(interface_tag_filter,v42rename)
	return_fields=patch(return_fields,v42rename)
	result=GetInterfaceTags.call(self,auth,interface_tag_filter,return_fields)
	return patch(result,v43rename)
