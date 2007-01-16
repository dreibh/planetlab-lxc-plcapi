from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.Slices import Slice, Slices

class SliceListNames(Method):
    """
    Deprecated. Can be implemented with GetSlices.

    List the names of registered slices.

    Users may only query slices of which they are members. PIs may
    query any of the slices at their sites. Admins may query any
    slice. If a slice that cannot be queried is specified in
    slice_filter, details about that slice will not be returned.
    """

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        Parameter(str, "Slice prefix", nullok = True)
        ]

    returns = [Slice.fields]
    

    def call(self, auth, prefix=None):

	slice_filter = None
        if prefix:
            slice_filter = {'name': prefix+'*'}
	
        slices = Slices(self.api, slice_filter)
        if not slices:
            raise PLCInvalidArgument, "No such slice"
	
	# If we are not admin, make sure to return only viewable
	# slices.
        if 'admin' not in self.caller['roles']:
            # Get slices that we are able to view
            valid_slice_ids = self.caller['slice_ids']
            if 'pi' in self.caller['roles'] and self.caller['site_ids']:
                sites = Sites(self.api, self.caller['site_ids'])
                for site in sites:
                    valid_slice_ids += site['slice_ids']

            if not valid_slice_ids:
                return []

            slices = filter(lambda slice: slice['slice_id'] in valid_slice_ids, slices)
	
	slice_names = [slice['name'] for slice in slices]

        return slice_names
