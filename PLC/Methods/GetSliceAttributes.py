from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.SliceAttributes import SliceAttribute, SliceAttributes
from PLC.Slices import Slice, Slices
from PLC.Nodes import Node, Nodes
from PLC.Auth import PasswordAuth

class GetSliceAttributes(Method):
    """
    Get an array of structs containing the values of slice and sliver
    attributes. An attribute is a sliver attribute if the node_id
    field is set. If slice_attribute_id_list is specified, only the
    specified attributes will be queried, if set.

    Users may only query attributes of slices or slivers of which they
    are members. PIs may only query attributes of slices or slivers at
    their sites, or of which they are members. Admins may query
    attributes of any slice or sliver.
    """

    roles = ['admin', 'pi', 'user']

    accepts = [
        PasswordAuth(),
        Mixed(Slice.fields['slice_id'],
              Slice.fields['name']),
        [SliceAttribute.fields['slice_attribute_id']],
        ]

    returns = [SliceAttribute.fields]

    def call(self, auth, slice_id_or_name, slice_attribute_id_list = None):
        slices = Slices(self.api, [slice_id_or_name]).values()
        if not slices:
            raise PLCInvalidArgument, "No such slice"
        slice = slices[0]

        if 'admin' not in self.caller['roles']:
            if self.caller['person_id'] in slice['person_ids']:
                pass
            elif 'pi' not in self.caller['roles']:
                raise PLCPermissionDenied, "Not a member of the specified slice"
            elif slice['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Specified slice not associated with any of your sites"

        if slice_attribute_id_list is None:
            slice_attribute_id_list = slice['slice_attribute_ids']
        else:
            if set(slice_attribute_id_list).intersection(slice['slice_attribute_ids']) != \
               set(slice_attribute_id_list):
                raise PLCInvalidArgument, "Invalid slice attribute ID(s)"

        slice_attributes = SliceAttributes(self.api, slice_attribute_id_list).values()
	# turn each slice attribute into a real dict
	slice_attributes = [dict(slice_attribute) \
			   for slice_attribute in slice_attributes]
	
        return slice_attributes
