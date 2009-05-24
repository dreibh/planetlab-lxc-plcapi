# $Id: $
from PLC.v42Legacy import patch
from PLC.v42LegacyAttributeTypes import v42rename, v43rename
from PLC.Methods.AddTagType import AddTagType
class AddSliceAttributeType(AddTagType):
    """ Legacy version of AddTagType. """
    skip_typecheck = True
    status = "deprecated"
    def call(self, auth, tag_type_fields):
	tag_type_fields=patch(tag_type_fields,v2rename)
	result=AddTagType.call(self,auth,tag_type_fields)
	return patch(result,v43rename)
