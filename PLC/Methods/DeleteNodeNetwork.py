# $Id: $
from PLC.v42Legacy import patch
from PLC.v42LegacyNodeNetworks import v42rename, v43rename
from PLC.Methods.DeleteInterface import DeleteInterface
class DeleteNodeNetwork(DeleteInterface):
    """ Legacy version of DeleteInterface. """
    skip_typecheck = True
    status = "deprecated"
    def call(self, auth, interface_id):
	interface_id=patch(interface_id,v42rename)
	result=DeleteInterface.call(self,auth,interface_id)
	return patch(result,v43rename)
