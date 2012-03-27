#
# Functions for interacting with the leases table in the database
#
# Thierry Parmentelat -- INRIA
#

from datetime import datetime

from PLC.Faults import *
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Table import Row, Table
from PLC.Nodes import Node, Nodes
from PLC.Slices import Slice, Slices
from PLC.LeaseFilter import LeaseFilter
from PLC.Timestamp import Timestamp

class Lease(Row):
    """
    Representation of a row in the leases table. To use, optionally
    instantiate with a dict of values. Update as you would a
    dict. Commit to the database with sync().
    """

    table_name = 'leases'
    primary_key = 'lease_id'
    join_tables = [ ]
    fields = {
        # native
        'lease_id': Parameter(int, "Lease identifier"),
        't_from': Timestamp.Parameter("timeslot start"),
        't_until': Timestamp.Parameter("timeslot end"),
        'node_id': Node.fields['node_id'],
        'slice_id': Slice.fields['slice_id'],

        # derived
        'hostname': Node.fields['hostname'],
        'node_type': Node.fields['node_type'],
        'name': Slice.fields['name'],
        'site_id': Slice.fields['site_id'],
        'duration': Parameter(int, "duration in seconds"),
        'expired' : Parameter(bool, "time slot is over"),
        }

    related_fields = { }

    def validate_time (self, timestamp, round_up):
        # convert to long
        timestamp = Timestamp.cast_long(timestamp)
        # retrieve configured granularity
        granularity = self.api.config.PLC_RESERVATION_GRANULARITY
        # the trick for rounding up rather than down
        if round_up: timestamp += (granularity-1)
        # round down
        timestamp = (timestamp/granularity) * granularity
        # return a SQL string
        return Timestamp.sql_validate_utc(timestamp)

    # round UP
    def validate_t_from(self,timestamp):
        return self.validate_time (timestamp, round_up=True)
    # round DOWN
    def validate_t_until (self, timestamp):
        return self.validate_time (timestamp, round_up=False)

class Leases(Table):
    """
    Representation of row(s) from the leases table in the
    database.
    """

    def __init__(self, api, lease_filter = None, columns = None):
        Table.__init__(self, api, Lease, columns)

        # the view that we're selecting upon: start with view_leases
        view = "view_leases"
        sql = "SELECT %s FROM %s WHERE true" % (", ".join(self.columns.keys()),view)


        if lease_filter is not None:
            if isinstance(lease_filter, (list, tuple, set, int, long)):
                lease_filter = Filter(Lease.fields, {'lease_id': lease_filter})
            elif isinstance(lease_filter, dict):
                lease_filter = LeaseFilter(Lease.fields, lease_filter)
            else:
                raise PLCInvalidArgument, "Wrong lease filter %r"%lease_filter
            sql += " AND (%s) %s" % lease_filter.sql(api)

        self.selectall(sql)
