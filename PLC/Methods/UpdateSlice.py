import time

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Slices import Slice, Slices
from PLC.Auth import PasswordAuth
from PLC.Sites import Site, Sites

can_update = lambda (field, value): field in \
             ['instantiation', 'url', 'description', 'max_nodes', 'expires']

class UpdateSlice(Method):
    """
    Updates the parameters of an existing slice with the values in
    slice_fields.

    Users may only update slices of which they are members. PIs may
    update any of the slices at their sites, or any slices of which
    they are members. Admins may update any slice.

    Only PIs and admins may update max_nodes. Slices cannot be renewed
    (by updating the expires parameter) more than 8 weeks into the
    future.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user']

    slice_fields = dict(filter(can_update, Slice.fields.items()))
    for field in slice_fields.values():
        field.optional = True

    accepts = [
        PasswordAuth(),
        Mixed(Slice.fields['slice_id'],
              Slice.fields['name']),
        slice_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, slice_id_or_name, slice_fields):
        slice_fields = dict(filter(can_update, slice_fields.items()))

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

        # Renewing
        if 'expires' in slice_fields and slice_fields['expires'] > slice['expires']:
            sites = Sites(self.api, [slice['site_id']]).values()
            assert sites
            site = sites[0]

            if site['max_slices'] < 0:
                raise PLCInvalidArgument, "Slice creation and renewal have been disabled for the site"

            # Maximum expiration date is 8 weeks from now
            # XXX Make this configurable
            max_expires = time.time() + (8 * 7 * 24 * 60 * 60)

            if 'admin' not in self.caller['roles'] and slice_fields['expires'] > max_expires:
                raise PLCInvalidArgument, "Cannot renew a slice beyond 8 weeks from now"

        if 'max_nodes' in slice_fields and slice_fields['max_nodes'] != slice['max_nodes']:
            if 'admin' not in self.caller['roles'] and \
               'pi' not in self.caller['roles']:
                raise PLCInvalidArgument, "Only admins and PIs may update max_nodes"

        slice.update(slice_fields)

        # XXX Make this a configurable policy
        if slice['description'] is None or not slice['description'].strip() or \
           slice['url'] is None or not slice['url'].strip():
            raise PLCInvalidArgument, "Cannot renew a slice with an empty description or URL"

        slice.sync()

        return 1
