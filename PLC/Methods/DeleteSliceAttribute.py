from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.SliceAttributes import SliceAttribute, SliceAttributes
from PLC.Slices import Slice, Slices
from PLC.Nodes import Node, Nodes
from PLC.Auth import Auth

class DeleteSliceAttribute(Method):
    """
    Deletes the specified slice or sliver attribute.

    Attributes may require the caller to have a particular role in
    order to be deleted. Users may only delete attributes of
    slices or slivers of which they are members. PIs may only delete
    attributes of slices or slivers at their sites, or of which they
    are members. Admins may delete attributes of any slice or sliver.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        SliceAttribute.fields['slice_attribute_id']
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, slice_attribute_id):
        slice_attributes = SliceAttributes(self.api, [slice_attribute_id])
        if not slice_attributes:
            raise PLCInvalidArgument, "No such slice attribute"
        slice_attribute = slice_attributes[0]
	PLCCheckLocalSliceAttribute(slice_attribute,"DeleteSliceAttribute")

        slices = Slices(self.api, [slice_attribute['slice_id']])
        if not slices:
            raise PLCInvalidArgument, "No such slice"
        slice = slices[0]
	PLCCheckLocalSlice(slice,"DeleteSliceAttribute")

        assert slice_attribute['slice_attribute_id'] in slice['slice_attribute_ids']

        if 'admin' not in self.caller['roles']:
            if self.caller['person_id'] in slice['person_ids']:
                pass
            elif 'pi' not in self.caller['roles']:
                raise PLCPermissionDenied, "Not a member of the specified slice"
            elif slice['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Specified slice not associated with any of your sites"

            if slice_attribute['min_role_id'] is not None and \
               min(self.caller['role_ids']) > slice_attribute['min_role_id']:
                raise PLCPermissioinDenied, "Not allowed to delete the specified attribute"

        slice_attribute.delete()
	self.object_ids = [slice_attribute['slice_attribute_id']]

        return 1
