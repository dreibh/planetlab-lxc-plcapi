# $Id: $
from PLC.v42Legacy import patch
from PLC.v42LegacyNodeNetworkSettingTypes import v42rename, v43rename
from PLC.Methods.UpdateTagType import UpdateTagType
class UpdateNodeNetworkSettingType(UpdateTagType):
    """ Legacy version of UpdateTagType. """
    status = "deprecated"
    def call(self, auth, tag_type_id_or_name, tag_type_fields):
	tag_type_id_or_name=patch(tag_type_id_or_name,v42rename)
	tag_type_fields=patch(tag_type_fields,v42rename)
	result=UpdateTagType.call(self,auth,tag_type_id_or_name,tag_type_fields)
	return patch(result,v43rename)
