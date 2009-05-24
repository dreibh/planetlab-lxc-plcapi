# $Id: $
from PLC.v42Legacy import patch
from PLC.v42LegacyNodeNetworkSettings import v42rename, v43rename
from PLC.Methods.AddInterfaceTag import AddInterfaceTag
class AddNodeNetworkSetting(AddInterfaceTag):
    """ Legacy version of AddInterfaceTag. """
    skip_typecheck = True
    status = "deprecated"
    def call(self, auth, interface_id, tag_type_id_or_name, value):
	interface_id=patch(interface_id,v42rename)
	tag_type_id_or_name=patch(tag_type_id_or_name,v42rename)
	value=patch(value,v42rename)
	result=AddInterfaceTag.call(self,auth,interface_id,tag_type_id_or_name,value)
	return patch(result,v43rename)
