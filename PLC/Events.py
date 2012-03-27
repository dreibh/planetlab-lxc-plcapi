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

class Event(Row):
    """
    Representation of a row in the events table.
    """

    table_name = 'events'
    primary_key = 'event_id'
    fields = {
        'event_id': Parameter(int, "Event identifier"),
        'person_id': Parameter(int, "Identifier of person responsible for event, if any"),
        'node_id': Parameter(int, "Identifier of node responsible for event, if any"),
        'auth_type': Parameter(int, "Type of auth used. i.e. AuthMethod"),
        'fault_code': Parameter(int, "Event fault code"),
        'call_name': Parameter(str, "Call responsible for this event"),
        'call': Parameter(str, "Call responsible for this event, including paramters"),
        'message': Parameter(str, "High level description of this event"),
        'runtime': Parameter(float, "Runtime of event"),
        'time': Parameter(int, "Date and time that the event took place, in seconds since UNIX epoch", ro = True),
        'object_ids': Parameter([int], "IDs of objects affected by this event"),
        'object_types': Parameter([str], "What type of object were affected by this event")
        }

    def add_object(self, object_type, object_id, commit = True):
        """
        Relate object to this event.
        """

        assert 'event_id' in self

        event_id = self['event_id']

        if 'object_ids' not in self:
            self['object_ids'] = []

        if object_id not in self['object_ids']:
            self.api.db.do("INSERT INTO event_object (event_id, object_id, object_type)" \
                           " VALUES(%(event_id)d, %(object_id)d, %(object_type)s)",
                           locals())

            if commit:
                self.api.db.commit()

            self['object_ids'].append(object_id)

class Events(Table):
    """
    Representation of row(s) from the events table in the database.
    """

    def __init__(self, api, event_filter = None, columns = None):
        Table.__init__(self, api, Event, columns)

        sql = "SELECT %s FROM view_events WHERE True" % \
              ", ".join(self.columns)

        if event_filter is not None:
            if isinstance(event_filter, (list, tuple, set, int, long)):
                event_filter = Filter(Event.fields, {'event_id': event_filter})
            elif isinstance(event_filter, dict):
                event_filter = Filter(Event.fields, event_filter)
            else:
                raise PLCInvalidArgument, "Wrong event object filter %r"%event_filter
            sql += " AND (%s) %s" % event_filter.sql(api)
        self.selectall(sql)
