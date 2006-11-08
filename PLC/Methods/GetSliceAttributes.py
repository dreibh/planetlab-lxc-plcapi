from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.SliceAttributes import SliceAttribute, SliceAttributes
from PLC.Sites import Site, Sites
from PLC.Slices import Slice, Slices
from PLC.Auth import Auth

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
        Auth(),
        Mixed([SliceAttribute.fields['slice_attribute_id']],
              Filter(SliceAttribute.fields))
        ]

    returns = [SliceAttribute.fields]

    def call(self, auth, slice_attribute_filter = None):
	# If we are not admin, make sure to only return our own slice
	# and sliver attributes.
        if 'admin' not in self.caller['roles']:
            # Get slices that we are able to view
            valid_slice_ids = self.caller['slice_ids']
            if 'pi' in self.caller['roles'] and self.caller['site_ids']:
                sites = Sites(self.api, self.caller['site_ids']).values()
                for site in sites:
                    valid_slice_ids += site['slice_ids']

            if not valid_slice_ids:
                return []

            # Get slice attributes that we are able to view
            valid_slice_attribute_ids = []
            slices = Slices(self.api, valid_slice_ids).values()
            for slice in slices:
                valid_slice_attribute_ids += slice['slice_attribute_ids']

            if not valid_slice_attribute_ids:
                return []

            if slice_attribute_filter is None:
                slice_attribute_filter = valid_slice_attribute_ids

        slice_attributes = SliceAttributes(self.api, slice_attribute_filter).values()

        # Filter out slice attributes that are not viewable
        if 'admin' not in self.caller['roles']:
            slice_attributes = filter(lambda slice_attribute: \
                                      slice_attribute['slice_attribute_id'] in valid_slice_attribute_ids,
                                      slice_attributes)

        return slice_attributes
