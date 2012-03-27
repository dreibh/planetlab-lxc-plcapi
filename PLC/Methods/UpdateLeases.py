from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.Timestamp import Timestamp, Duration

from PLC.Leases import Lease, Leases
from PLC.Slices import Slice, Slices

can_update = lambda (field, value): field in ['t_from', 't_until', 'duration']

class UpdateLeases(Method):
    """
    Updates the parameters of a (set of) existing lease(s) with the values in
    lease_fields; specifically this applies to the timeslot definition.
    As a convenience you may, in addition to the t_from and t_until fields,
    you can also set the 'duration' field.

    Users may only update leases attached to their slices.
    PIs may update any of the leases for slices at their sites, or any
    slices of which they are members. Admins may update any lease.

    Returns a dict of successfully updated lease_ids and error messages.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    lease_fields = dict(filter(can_update, Lease.fields.items()))

    accepts = [
        Auth(),
        Mixed (Lease.fields['lease_id'],
               [Lease.fields['lease_id']]),
        lease_fields
        ]

    returns = Parameter(dict, " 'updated_ids' is the list ids updated, 'errors' is a list of error strings")

    debug=False
#    debug=True

    def call(self, auth, lease_ids, input_fields):
        input_fields = dict(filter(can_update, input_fields.items()))

        if 'duration' in input_fields:
            if 't_from' in input_fields and 't_until' in input_fields:
                raise PLCInvalidArgument, "Cannot set t_from AND t_until AND duration"
            # specify 'duration':0 to keep duration unchanged
            if input_fields['duration'] : input_fields['duration']=Duration.validate(input_fields['duration'])

        # Get lease information
        leases = Leases(self.api, lease_ids)
        if not leases:
            raise PLCInvalidArgument, "No such leases %r"%lease_ids

        # fetch related slices
        slices = Slices(self.api, [ lease['slice_id'] for lease in leases],['slice_id','person_ids'])
        # create hash on slice_id
        slice_map = dict ( [ (slice['slice_id'],slice) for slice in slices ] )

        updated_ids=[]
        errors=[]

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

            try:
                # we've ruled out already the case where all 3 (from, to, duration) where specified
                if 'duration' not in input_fields:
                    lease_fields=input_fields
                else:
                    # all arithmetics on longs..
                    duration=Duration.validate(input_fields['duration'])
                    # specify 'duration':0 to keep duration unchanged
                    if not duration:
                        duration = Timestamp.cast_long(lease['t_until'])-Timestamp.cast_long(lease['t_from'])
                    if 't_from' in input_fields:
                        lease_fields={'t_from':input_fields['t_from'],
                                      't_until':Timestamp.cast_long(input_fields['from'])+duration}
                    elif 't_until' in input_fields:
                        lease_fields={'t_from':Timestamp.cast_long(input_fields['t_until'])-duration,
                                      't_until':input_fields['t_until']}
                    else:
                        lease_fields={'t_until':Timestamp.cast_long(lease['t_from'])+duration}
                if UpdateLeases.debug:
                    print 'lease_fields',lease_fields
                    for k in [ 't_from', 't_until'] :
                        if k in lease_fields: print k,'aka',Timestamp.sql_validate_utc(lease_fields[k])

                lease.update(lease_fields)
                lease.sync()
                updated_ids.append(lease['lease_id'])
            except Exception,e:
                errors.append("Could not update lease %d - check new time limits ? -- %r"%(lease['lease_id'],e))

        # Logging variables
        self.event_objects = {'Lease': updated_ids}
        self.message = 'lease %r updated: %s' %  (lease_ids, ", ".join(input_fields.keys()))

        return {'updated_ids' : updated_ids,
                'errors' : errors }
