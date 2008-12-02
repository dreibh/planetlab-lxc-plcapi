# $Id$
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.SliceTags import SliceTag, SliceTags
from PLC.Slices import Slice, Slices
from PLC.Nodes import Node, Nodes
from PLC.Auth import Auth

class DeleteSliceTag(Method):
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
        SliceTag.fields['slice_tag_id']
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, slice_tag_id):
        slice_tags = SliceTags(self.api, [slice_tag_id])
        if not slice_tags:
            raise PLCInvalidArgument, "No such slice attribute"
        slice_tag = slice_tags[0]

        slices = Slices(self.api, [slice_tag['slice_id']])
        if not slices:
            raise PLCInvalidArgument, "No such slice"
        slice = slices[0]

        assert slice_tag['slice_tag_id'] in slice['slice_tag_ids']

        if 'admin' not in self.caller['roles']:
            if self.caller['person_id'] in slice['person_ids']:
                pass
            elif 'pi' not in self.caller['roles']:
                raise PLCPermissionDenied, "Not a member of the specified slice"
            elif slice['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Specified slice not associated with any of your sites"

            if slice_tag['min_role_id'] is not None and \
               min(self.caller['role_ids']) > slice_tag['min_role_id']:
                raise PLCPermissioinDenied, "Not allowed to delete the specified attribute"

        slice_tag.delete()
	self.event_objects = {'SliceTag': [slice_tag['slice_tag_id']]}

        return 1
