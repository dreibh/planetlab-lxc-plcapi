# $Id: $
from PLC.v42Legacy import patch
from PLC.v42LegacyNodeNetworks import v42rename, v43rename
from PLC.Methods.AddInterface import AddInterface
class AddNodeNetwork(AddInterface):
    """ Legacy version of AddInterface. """
    skip_typecheck = True
    status = "deprecated"
    def call(self, auth, node_id_or_hostname, interface_fields):
	node_id_or_hostname=patch(node_id_or_hostname,v2rename)
	interface_fields=patch(interface_fields,v2rename)
	result=AddInterface.call(self,auth,node_id_or_hostname,interface_fields)
	return patch(result,v43rename)
