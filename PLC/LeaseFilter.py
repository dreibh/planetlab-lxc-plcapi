#
# Thierry Parmentelat -- INRIA
#
# Utilities for filtering on leases

import time
import calendar

from PLC.Faults import *
from PLC.Filter import Filter
from PLC.Parameter import Parameter, Mixed
from PLC.Timestamp import Timestamp

# supersede the generic Filter class to support time intersection


class LeaseFilter (Filter):

    # general notes on input parameters
    # int_timestamp: number of seconds since the epoch
    # str_timestamp: see Timestamp.sql_validate
    # timeslot: a tuple (from, until), each being either int_timestamp or
    # str_timestamp

    local_fields = {
        'alive': Mixed(
            Parameter(
                int,  "int_timestamp: leases alive at that time"),
            Parameter(
                str,  "str_timestamp: leases alive at that time"),
            Parameter(
                tuple, "timeslot: the leases alive during this timeslot")),
        'clip':  Mixed(
            Parameter(
                int,  "int_timestamp: leases alive after that time"),
            Parameter(
                str,  "str_timestamp: leases alive after at that time"),
            Parameter(
                tuple, "timeslot: the leases alive during this timeslot")),
        ########## macros
        # {'day' : 0} : all leases from today and on
        # {'day' : 1} : all leases today (localtime at the myplc)
        # {'day' : 2} : all leases today and tomorrow (localtime at the myplc)
        # etc..
        'day': Parameter(int, "clip on a number of days from today and on;"
                         " 0 means no limit in the future"),
    }

    def __init__(self, fields={}, filter={},
                 doc="Lease filter -- adds the 'alive' and 'clip'"
                 "capabilities for filtering on leases"):
        Filter.__init__(self, fields, filter, doc)
        self.fields.update(LeaseFilter.local_fields)

    # canonical type
    @staticmethod
    def quote(timestamp): return Timestamp.cast_long(timestamp)

    # basic SQL utilities
    @staticmethod
    def sql_time_intersect(f1, u1, f2, u2):
        # either f2 is in [f1,u1], or u2 is in [f1,u1], or f2<=f1<=u1<=u2
        return ("(({f1} <= {f2}) AND ({f2} <= {u1})) " +
                "OR (({f1} <= {u2}) AND ({u2} <= {u1})) " +
                "OR (({f2}<={f1}) AND ({u1}<={u2}))").format(**locals())

    @staticmethod
    def time_in_range(timestamp, f1, u1):
        return Timestamp.cast_long(f1) <= Timestamp.cast_long(timestamp) \
            and Timestamp.cast_long(timestamp) <= Timestamp.cast_long(u1)

    @staticmethod
    def sql_time_in_range(timestamp, f1, u1):
        # is timestamp in [f1, u1]
        return "(({f1} <= {timestamp}) AND ({timestamp} <= {u1}))"\
            .format(**locals())

    @staticmethod
    def sql_timeslot_after(f1, u1, mark):
        # is the lease alive after mark, i.e. u1 >= mark
        return "({u1} >= {mark})".format(**locals())

    # hooks for the local fields
    def sql_alive(self, alive):
        if isinstance(alive, int) or isinstance(alive, str):
            # the lease is alive at that time if from <= alive <= until
            alive = LeaseFilter.quote(alive)
            return LeaseFilter.sql_time_in_range(alive, 't_from', 't_until')
        elif isinstance(alive, tuple):
            (f, u) = alive
            f = LeaseFilter.quote(f)
            u = LeaseFilter.quote(u)
            return LeaseFilter.sql_time_intersect(f, u, 't_from', 't_until')
        else:
            raise PLCInvalidArgument("LeaseFilter: alive field {}"
                                     .format(alive))

    def sql_clip(self, clip):
        if isinstance(clip, int) or isinstance(clip, str):
            start = LeaseFilter.quote(clip)
            return LeaseFilter.sql_timeslot_after('t_from', 't_until', start)
        elif isinstance(clip, tuple):
            (f, u) = clip
            f = LeaseFilter.quote(f)
            u = LeaseFilter.quote(u)
            return LeaseFilter.sql_time_intersect(f, u, 't_from', 't_until')
        else:
            raise PLCInvalidArgument("LeaseFilter: clip field {}"
                                     .format(clip))

    # the whole key to implementing day is to compute today's beginning
    def today_start(self):
        # a struct_time
        st = time.localtime()
        seconds_today = st.tm_hour * 3600 + st.tm_min * 60 + st.tm_sec
        return int(time.time()) - seconds_today

    # supersede the generic Filter 'sql' method
    def sql(self, api, join_with="AND"):
        # implement 'day' as a clip
        if 'day' in self:
            if 'clip' in self:
                raise PLCInvalidArgument("LeaseFilter cannot have both 'clip' and 'day'")
            today = self.today_start()
            nb_days = self['day']
            if nb_days == 0:
                self['clip'] = today
            else:
                self['clip'] = (today, today + nb_days * 24 * 3600)
            del self['day']

        # preserve locally what belongs to us, hide it from the superclass
        # self.local is a dict    local_key : user_value
        # self.negation is a dict  local_key : string
        self.local = {}
        self.negation = {}
        for (k, v) in list(LeaseFilter.local_fields.items()):
            if k in self:
                self.local[k] = self[k]
                del self[k]
                self.negation[k] = ""
            elif ('~' + k) in self:
                self.local[k] = self['~' + k]
                del self['~' + k]
                self.negation[k] = "NOT "
        # run the generic filtering code
        (where_part, clip_part) = Filter.sql(self, api, join_with)
        for (k, v) in list(self.local.items()):
            try:
                # locate hook function associated with key
                method = LeaseFilter.__dict__['sql_' + k]
                where_part += " {} {}({})"\
                              .format(self.join_with,
                                      self.negation[k],
                                      method(self, self.local[k]))
            except Exception as e:
                raise PLCInvalidArgument(
                    "LeaseFilter: something wrong with filter"
                    "key {}, val was {} -- {}".format(k, v, e))
        return (where_part, clip_part)

# xxx not sure where this belongs yet
# given a set of nodes, and a timeslot,
# returns the available leases that have at least a given duration


def free_leases(api, node_ids, t_from, t_until, min_duration):

    # get the leases for these nodes and timeslot
    filter = {'node_id': node_ids,
              'clip': (t_from, t_until),
              # sort by node, and inside one node, chronologically
              '-SORT': ('node_id', 't_from'),
              }
    leases = Leases(api, filter)

    result = []

    # sort node_ids
    node_ids.sort()

    # scan nodes from the input
    input_node_id = 0
    # scan nodes from the leases
    lease_node_id = 0

    return '?? what now ??'


def node_free_leases(node_id, node_leases, t_from, t_until):

    # no lease yet : return one solid lease
    if not node_leases:
        return [{'node_id': node_id,
                 't_from': t_from,
                 't_until': t_until}]

    result = []
    current_time = t_from
    is_on = LeaseFilter.time_in_range(
        node_leases[0]['t_from'], t_from, t_until)

    while True:
        # print 'DBG','current_time',current_time,'is_on',is_on,'result',result
        # lease is active
        if is_on:
            current_time = node_leases[0]['t_until']
            is_on = False
            del node_leases[0]
            if not node_leases:
                return result
        # free, has no remaining lease
        elif not node_leases:
            result.append(
                {'node_id': node_id,
                 't_from': current_time, 't_until': t_until})
            return result
        # free and has remaining leases
        else:
            next_time = node_leases[0]['t_from']
            result.append(
                {'node_id': node_id,
                 't_from': current_time, 't_until': next_time})
            current_time = next_time
            is_on = True
