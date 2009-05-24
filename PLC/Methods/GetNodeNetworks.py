# $Id: $
from PLC.v42Legacy import patch
from PLC.v42LegacyNodeNetworks import v42rename, v43rename
from PLC.Methods.GetInterfaces import GetInterfaces
class GetNodeNetworks(GetInterfaces):
    """ Legacy version of GetInterfaces. """
    skip_typecheck = True
    status = "deprecated"
    def call(self, auth, interface_filter = None, return_fields = None):
	interface_filter=patch(interface_filter,v42rename)
	return_fields=patch(return_fields,v42rename)
	result=GetInterfaces.call(self,auth,interface_filter,return_fields)
	return patch(result,v43rename)
