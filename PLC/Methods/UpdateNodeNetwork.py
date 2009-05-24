# $Id: $
from PLC.v42Legacy import patch
from PLC.v42LegacyNodeNetworks import v42rename, v43rename
from PLC.Methods.UpdateInterface import UpdateInterface
class UpdateNodeNetwork(UpdateInterface):
    """ Legacy version of UpdateInterface. """
    status = "deprecated"
    def call(self, auth, interface_id, interface_fields):
	interface_id=patch(interface_id,v42rename)
	interface_fields=patch(interface_fields,v42rename)
	result=UpdateInterface.call(self,auth,interface_id,interface_fields)
	return patch(result,v43rename)
