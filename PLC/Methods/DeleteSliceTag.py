#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.SliceTags import SliceTag, SliceTags
from PLC.Slices import Slice, Slices
from PLC.Nodes import Node, Nodes

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

    roles = ['admin', 'pi', 'user', 'tech']

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
            raise PLCInvalidArgument, "No such slice %d"%slice_tag['slice_id']
        slice = slices[0]

        assert slice_tag['slice_tag_id'] in slice['slice_tag_ids']

        # check authorizations
        node_id_or_hostname=slice_tag['node_id']
        nodegroup_id_or_name=slice_tag['nodegroup_id']
        slice.caller_may_write_tag(self.api,self.caller,tag_type,node_id_or_hostname,nodegroup_id_or_name)

        slice_tag.delete()
        self.event_objects = {'SliceTag': [slice_tag['slice_tag_id']]}

        return 1
