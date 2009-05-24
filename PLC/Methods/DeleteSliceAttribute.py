# $Id: $
from PLC.v42Legacy import patch
from PLC.v42LegacySliceAttributes import v42rename, v43rename
from PLC.Methods.DeleteSliceTag import DeleteSliceTag
class DeleteSliceAttribute(DeleteSliceTag):
    """ Legacy version of DeleteSliceTag. """
    status = "deprecated"
    def call(self, auth, slice_tag_id):
	slice_tag_id=patch(slice_tag_id,v42rename)
	result=DeleteSliceTag.call(self,auth,slice_tag_id)
	return patch(result,v43rename)
