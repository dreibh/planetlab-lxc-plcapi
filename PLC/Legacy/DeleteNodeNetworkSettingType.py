# $Id: $
from PLC.v42Legacy import patch
from PLC.v42LegacyNodeNetworkSettingTypes import v42rename, v43rename
from PLC.Methods.DeleteTagType import DeleteTagType
class DeleteNodeNetworkSettingType(DeleteTagType):
    """ Legacy version of DeleteTagType. """
    status = "deprecated"
    def call(self, auth, tag_type_id_or_name):
	tag_type_id_or_name=patch(tag_type_id_or_name,v42rename)
	result=DeleteTagType.call(self,auth,tag_type_id_or_name)
	return patch(result,v43rename)