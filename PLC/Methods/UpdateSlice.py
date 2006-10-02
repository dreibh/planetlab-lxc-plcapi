import time

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Slices import Slice, Slices
from PLC.Auth import PasswordAuth
from PLC.Sites import Site, Sites

class UpdateSlice(Method):
    """
    Updates the parameters of an existing slice with the values in
    update_fields.

    Users may only update slices of which they are members. PIs may
    update any of the slices at their slices. Admins may update any
    slice.

    Only PIs and admins may update max_nodes. Slices cannot be renewed
    (by updating the expires parameter) more than 8 weeks into the
    future.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user']

    can_update = lambda (field, value): field in \
                 ['instantiation', 'url', 'description', 'max_nodes', 'expires']
    update_fields = dict(filter(can_update, Slice.fields.items()))

    accepts = [
        PasswordAuth(),
        Mixed(Slice.fields['slice_id'],
              Slice.fields['name']),
        update_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, slice_id_or_name, update_fields):
        if filter(lambda field: field not in self.update_fields, update_fields):
            raise PLCInvalidArgument, "Invalid field specified"

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
        if 'expires' in update_fields and update_fields['expires'] > slice['expires']:
            sites = Sites(self.api, [slice['site_id']]).values()
            assert sites
            site = sites[0]

            if site['max_slices'] < 0:
                raise PLCInvalidArgument, "Slice creation and renewal have been disabled for the site"

            # Maximum expiration date is 8 weeks from now
            # XXX Make this configurable
            max_expires = time.time() + (8 * 7 * 24 * 60 * 60)

            if 'admin' not in self.caller['roles'] and update_fields['expires'] > max_expires:
                raise PLCInvalidArgument, "Cannot renew a slice beyond 8 weeks from now"

        if 'max_nodes' in update_fields and update_fields['max_nodes'] != slice['max_nodes']:
            if 'admin' not in self.caller['roles'] and \
               'pi' not in self.caller['roles']:
                raise PLCInvalidArgument, "Only admins and PIs may update max_nodes"

        slice.update(update_fields)

        # XXX Make this a configurable policy
        if slice['description'] is None or not slice['description'].strip() or \
           slice['url'] is None or not slice['url'].strip():
            raise PLCInvalidArgument, "Cannot renew a slice with an empty description or URL"

        slice.sync()

        return 1
