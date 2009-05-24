# $Id: $
from PLC.v42Legacy import patch
from PLC.v42LegacyAttributeTypes import v42rename, v43rename
from PLC.Methods.UpdateTagType import UpdateTagType
class UpdateSliceAttributeType(UpdateTagType):
    """ Legacy version of UpdateTagType. """
    skip_typecheck = True
    status = "deprecated"
    def call(self, auth, tag_type_id_or_name, tag_type_fields):
	tag_type_id_or_name=patch(tag_type_id_or_name,v2rename)
	tag_type_fields=patch(tag_type_fields,v2rename)
	result=UpdateTagType.call(self,auth,tag_type_id_or_name,tag_type_fields)
	return patch(result,v43rename)
