# $Id: $
from PLC.v42Legacy import patch
from PLC.v42LegacySliceAttributes import v42rename, v43rename
from PLC.Methods.AddSliceTag import AddSliceTag
class AddSliceAttribute(AddSliceTag):
    """ Legacy version of AddSliceTag. """
    skip_typecheck = True
    status = "deprecated"
    def call(self, auth, slice_id_or_name, tag_type_id_or_name, value, node_id_or_hostname = None, nodegroup_id_or_name = None):
	slice_id_or_name=patch(slice_id_or_name,v2rename)
	tag_type_id_or_name=patch(tag_type_id_or_name,v2rename)
	value=patch(value,v2rename)
	node_id_or_hostname=patch(node_id_or_hostname,v2rename)
	nodegroup_id_or_name=patch(nodegroup_id_or_name,v2rename)
	result=AddSliceTag.call(self,auth,slice_id_or_name,tag_type_id_or_name,value,node_id_or_hostname,nodegroup_id_or_name)
	return patch(result,v43rename)
