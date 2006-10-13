from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import PasswordAuth
from PLC.Slices import Slice, Slices

class GetSlices(Method):
    """
    Return an array of structs containing details about slices. If
    slice_id_or_name_list is specified, only the specified slices will
    be queried.

    Users may only query slices of which they are members. PIs may
    query any of the slices at their sites. Admins may query any
    slice. If a slice that cannot be queried is specified in
    slice_id_or_name_list, details about that slice will not be
    returned.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        [Mixed(Slice.fields['slice_id'],
               Slice.fields['name'])],
        Parameter([str], 'List of fields to return')
        ]

    returns = [Slice.fields]

    def call(self, auth, slice_id_or_name_list = None):
        # Get slice information
        slices = Slices(self.api, slice_id_or_name_list).values()

        # Filter out slices that are not viewable
        if 'admin' not in self.caller['roles']:
            member_of = lambda slice: self.caller['person_id'] in slice['person_ids']
            if 'pi' in self.caller['roles']:
                can_view = lambda slice: \
                           member_of(slice) or \
                           slice['site_id'] in self.caller['site_ids']
            else:
                can_view = member_of
            slices = filter(can_view, slices)

	# turn each slice into a real dict
	slices = [dict(slice.items()) for slice in slices]

        return slices
