import re

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Slices import Slice, Slices
from PLC.Auth import Auth
from PLC.Sites import Site, Sites

can_update = lambda (field, value): field in \
             ['name', 'instantiation', 'url', 'description', 'max_nodes']

class AddSlice(Method):
    """
    Adds a new slice. Any fields specified in slice_fields are used,
    otherwise defaults are used.

    Valid slice names are lowercase and begin with the login_base
    (slice prefix) of a valid site, followed by a single
    underscore. Thereafter, only letters, numbers, or additional
    underscores may be used.

    PIs may only add slices associated with their own sites (i.e.,
    slice prefixes must always be the login_base of one of their
    sites).

    Returns the new slice_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin', 'pi']

    slice_fields = dict(filter(can_update, Slice.fields.items()))

    accepts = [
        Auth(),
        slice_fields
        ]

    returns = Parameter(int, 'New slice_id (> 0) if successful')

    event_type = 'Add'
    object_type = 'Slice'

    def call(self, auth, slice_fields):
        slice_fields = dict(filter(can_update, slice_fields.items()))

        # 1. Lowercase.
        # 2. Begins with login_base (only letters).
        # 3. Then single underscore after login_base.
        # 4. Then letters, numbers, or underscores.
        name = slice_fields['name']
        good_name = r'^[a-z]+_[a-z0-9_]+$'
        if not name or \
           not re.match(good_name, name):
            raise PLCInvalidArgument, "Invalid slice name"

        # Get associated site details
        login_base = name.split("_")[0]
        sites = Sites(self.api, [login_base])
        if not sites:
            raise PLCInvalidArgument, "Invalid slice prefix"
        site = sites[0]

        if 'admin' not in self.caller['roles']:
            if site['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Slice prefix must be the same as the login_base of one of your sites"

        if len(site['slice_ids']) >= site['max_slices']:
            raise PLCInvalidArgument, "Site has reached its maximum allowable slice count"

        slice = Slice(self.api, slice_fields)
        slice['creator_person_id'] = self.caller['person_id']
        slice['site_id'] = site['site_id']
        slice.sync()

	self.object_ids = [slice['slice_id']]

        return slice['slice_id']
