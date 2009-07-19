# $Id$
# $URL$
from PLC.v42Legacy import patch
from PLC.v42LegacySliceAttributeTypes import v42rename, v43rename
from PLC.Methods.GetTagTypes import GetTagTypes
class GetSliceAttributeTypes(GetTagTypes):
    """ Legacy version of GetTagTypes. """
    status = "deprecated"
    def call(self, auth, tag_type_filter = None, return_fields = None):
	tag_type_filter=patch(tag_type_filter,v42rename)
	return_fields=patch(return_fields,v42rename)
	result=GetTagTypes.call(self,auth,tag_type_filter,return_fields)
	return patch(result,v43rename)
