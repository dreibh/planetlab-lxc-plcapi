# Thierry Parmentelat -- INRIA

from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.Leases import Lease, Leases, LeaseFilter

class GetLeases(Method):
    """
    Returns an array of structs containing details about leases. If
    lease_filter is specified and is an array of lease identifiers or
    lease names, or a struct of lease attributes, only leases matching
    the filter will be returned. If return_fields is specified, only the
    specified details will be returned.

    All leases are exposed to all users.

    In addition to the usual filter capabilities, the following are supported:
     * GetLeases ({ 'alive' : '2010-02-20 20:00' , <regular_filter_fields...> })
       returns the leases that are active at that point in time
     * GetLeases ({ 'alive' : ('2010-02-20 20:00' , '2010-02-20 21:00' ) , ... })
       ditto for a time range

    This is implemented in the LeaseFilter class; negation actually is supported
    through the usual '~alive' form, although maybe not really useful.

    """

    roles = ['admin', 'pi', 'user', 'node']

    accepts = [
        Auth(),
        Mixed(Lease.fields['lease_id'],
              [Lease.fields['lease_id']],
              LeaseFilter(Lease.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [Lease.fields]

    def call(self, auth, lease_filter = None, return_fields = None):

        # Must query at least lease_id (see below)
        if return_fields is not None and 'lease_id' not in return_fields:
            return_fields.append('lease_id')
            added_fields = True
        else:
            added_fields = False

        leases = Leases(self.api, lease_filter, return_fields)

        # Remove lease_id if not specified
        if added_fields:
            for lease in leases:
                if 'lease_id' in lease:
                    del lease['lease_id']

        return leases
