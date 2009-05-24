# $Id: $
from PLC.v42Legacy import patch
from PLC.v42LegacyAttributeTypes import v42rename, v43rename
from PLC.Methods.DeleteTagType import DeleteTagType
class DeleteSliceAttributeType(DeleteTagType):
    """ Legacy version of DeleteTagType. """
    skip_typecheck = True
    status = "deprecated"
    def call(self, auth, tag_type_id_or_name):
	tag_type_id_or_name=patch(tag_type_id_or_name,v2rename)
	result=DeleteTagType.call(self,auth,tag_type_id_or_name)
	return patch(result,v43rename)
