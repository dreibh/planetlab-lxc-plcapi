from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth
from PLC.Leases import Lease, Leases
from PLC.Slices import Slice, Slices

class DeleteLeases(Method):
    """
    Deletes a lease.

    Users may only delete leases attached to their slices.
    PIs may delete any of the leases for slices at their sites, or any
    slices of which they are members. Admins may delete any lease.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    accepts = [
        Auth(),
        Mixed(Lease.fields['lease_id'],[ Lease.fields['lease_id']]),
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, lease_ids):
        # Get associated lease details
        leases = Leases(self.api, lease_ids)
        if len(leases) != len(lease_ids):
            raise PLCInvalidArgument, "Could not find all leases %r"%lease_ids

        # fetch related slices
        slices = Slices(self.api, [ lease['slice_id'] for lease in leases],['slice_id','person_ids'])
        # create hash on slice_id
        slice_map = dict ( [ (slice['slice_id'],slice) for slice in slices ] )

        lease_ids=[lease['lease_id'] for lease in leases]
        for lease in leases:
            if 'admin' not in self.caller['roles']:
                slice=slice_map[lease['slice_id']]
                # check slices only once
                if not slice.has_key('verified'):
                    if self.caller['person_id'] in slice['person_ids']:
                        pass
                    elif 'pi' not in self.caller['roles']:
                        raise PLCPermissionDenied, "Not a member of slice %r"%slice['name']
                    elif slice['site_id'] not in self.caller['site_ids']:
                        raise PLCPermissionDenied, "Slice %r not associated with any of your sites"%slice['name']
                slice['verified']=True

            lease.delete()

        # Logging variables
        self.event_objects = {'Lease': lease_ids }
        self.message = 'Leases %r deleted' % lease_ids

        return 1
