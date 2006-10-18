from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.SliceAttributes import SliceAttribute, SliceAttributes
from PLC.Sites import Site, Sites
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
        [SliceAttribute.fields['slice_attribute_id']],
        ]

    returns = [SliceAttribute.fields]

    def call(self, auth, slice_attribute_ids = None):
	# If we are not admin, make sure to only return our own slice
	# and sliver attributes.
        if 'admin' not in self.caller['roles']:
            # Get list of slices that we are able to view
            slices = Slices(self.api, self.caller['slice_ids']).values()
            if 'pi' in self.caller['roles']:
                sites = Sites(self.api, self.caller['site_ids']).values()
                slices += Slices(self.api, sites['slice_ids']).values()

            valid_slice_attribute_ids = set()
            for slice in slices:
                valid_slice_attribute_ids = valid_slice_attribute_ids.union(slice['slice_attribute_ids'])

            if not slice_attribute_ids:
                slice_attribute_ids = valid_slice_attribute_ids
            else:
                slice_attribute_ids = valid_slice_attribute_ids.intersection(slice_attribute_ids)

        slice_attributes = SliceAttributes(self.api, slice_attribute_ids).values()

	slice_attributes = [dict(slice_attribute) for slice_attribute in slice_attributes]
	
        return slice_attributes
