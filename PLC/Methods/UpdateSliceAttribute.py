# $Id: $
from PLC.v42Legacy import patch
from PLC.v42LegacySliceAttributes import v42rename, v43rename
from PLC.Methods.UpdateSliceTag import UpdateSliceTag
class UpdateSliceAttribute(UpdateSliceTag):
    """ Legacy version of UpdateSliceTag. """
    status = "deprecated"
    def call(self, auth, slice_tag_id, value):
	slice_tag_id=patch(slice_tag_id,v42rename)
	value=patch(value,v42rename)
	result=UpdateSliceTag.call(self,auth,slice_tag_id,value)
	return patch(result,v43rename)
