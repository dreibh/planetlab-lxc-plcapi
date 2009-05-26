# $Id: $
from PLC.v42Legacy import patch
from PLC.v42LegacySliceAttributes import v42rename, v43rename
from PLC.Methods.GetSliceTags import GetSliceTags
class GetSliceAttributes(GetSliceTags):
    """ Legacy version of GetSliceTags. """
    status = "deprecated"
    def call(self, auth, slice_tag_filter = None, return_fields = None):
	slice_tag_filter=patch(slice_tag_filter,v42rename)
	return_fields=patch(return_fields,v42rename)
	result=GetSliceTags.call(self,auth,slice_tag_filter,return_fields)
	return patch(result,v43rename)
