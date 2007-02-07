from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.SliceAttributes import SliceAttribute, SliceAttributes
from PLC.Persons import Person, Persons
from PLC.Sites import Site, Sites
from PLC.Slices import Slice, Slices
from PLC.Auth import Auth

class GetSliceAttributes(Method):
    """
    Returns an array of structs containing details about slice and
    sliver attributes. An attribute is a sliver attribute if the
    node_id field is set. If slice_attribute_filter is specified and
    is an array of slice attribute identifiers, or a struct of slice
    attribute attributes, only slice attributes matching the filter
    will be returned. If return_fields is specified, only the
    specified details will be returned.

    Users may only query attributes of slices or slivers of which they
    are members. PIs may only query attributes of slices or slivers at
    their sites, or of which they are members. Admins may query
    attributes of any slice or sliver.
    """

    roles = ['admin', 'pi', 'user', 'node']

    accepts = [
        Auth(),
        Mixed([SliceAttribute.fields['slice_attribute_id']],
              Filter(SliceAttribute.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [SliceAttribute.fields]
    

    def call(self, auth, slice_attribute_filter = None, return_fields = None):
	# If we are not admin, make sure to only return our own slice
	# and sliver attributes.
        if isinstance(self.caller, Person) and \
           'admin' not in self.caller['roles']:
            # Get slices that we are able to view
            valid_slice_ids = self.caller['slice_ids']
            if 'pi' in self.caller['roles'] and self.caller['site_ids']:
                sites = Sites(self.api, self.caller['site_ids'])
                for site in sites:
                    valid_slice_ids += site['slice_ids']

            if not valid_slice_ids:
                return []

            # Get slice attributes that we are able to view
            valid_slice_attribute_ids = []
            slices = Slices(self.api, valid_slice_ids)
            for slice in slices:
                valid_slice_attribute_ids += slice['slice_attribute_ids']

            if not valid_slice_attribute_ids:
                return []

            if slice_attribute_filter is None:
                slice_attribute_filter = valid_slice_attribute_ids

        # Must query at least slice_attribute_id (see below)
        if return_fields is not None and 'slice_attribute_id' not in return_fields:
            return_fields.append('slice_attribute_id')
            added_fields = True
        else:
            added_fields = False

        slice_attributes = SliceAttributes(self.api, slice_attribute_filter, return_fields)

        # Filter out slice attributes that are not viewable
        if isinstance(self.caller, Person) and \
           'admin' not in self.caller['roles']:
            slice_attributes = filter(lambda slice_attribute: \
                                      slice_attribute['slice_attribute_id'] in valid_slice_attribute_ids,
                                      slice_attributes)

        # Remove slice_attribute_id if not specified
        if added_fields:
            for slice_attribute in slice_attributes:
                del slice_attribute['slice_attribute_id']

        return slice_attributes
