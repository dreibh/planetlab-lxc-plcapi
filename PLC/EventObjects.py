#
# Functions for interacting with the events table in the database
#
# Tony Mack <tmack@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Debug import profile
from PLC.Table import Row, Table

class EventObject(Row):
    """
    Representation of a row in the event_object table.
    """

    table_name = 'event_object'
    primary_key = 'event_id'
    fields = {
        'event_id': Parameter(int, "Event identifier"),
        'person_id': Parameter(int, "Identifier of person responsible for event, if any"),
        'node_id': Parameter(int, "Identifier of node responsible for event, if any"),
        'fault_code': Parameter(int, "Event fault code"),
        'call_name': Parameter(str, "Call responsible for this event"),
        'call': Parameter(str, "Call responsible for this event, including paramters"),
        'message': Parameter(str, "High level description of this event"),
        'runtime': Parameter(float, "Runtime of event"),
        'time': Parameter(int, "Date and time that the event took place, in seconds since UNIX epoch", ro = True),
        'object_id': Parameter(int, "ID of objects affected by this event"),
        'object_type': Parameter(str, "What type of object is this event affecting")
        }

class EventObjects(Table):
    """
    Representation of row(s) from the event_object table in the database.
    """

    def __init__(self, api, event_filter = None, columns = None):
        Table.__init__(self, api, EventObject, columns)

        sql = "SELECT %s FROM view_event_objects WHERE True" % \
            ", ".join(self.columns)

        if event_filter is not None:
            if isinstance(event_filter, (list, tuple, set, int, long)):
                event_filter = Filter(EventObject.fields, {'event_id': event_filter})
                sql += " AND (%s) %s" % event_filter.sql(api, "OR")
            elif isinstance(event_filter, dict):
                event_filter = Filter(EventObject.fields, event_filter)
                sql += " AND (%s) %s" % event_filter.sql(api, "AND")
            else:
                raise PLCInvalidArgument, "Wrong event object filter %r"%event_filter

        self.selectall(sql)
