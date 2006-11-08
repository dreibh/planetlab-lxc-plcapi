#
# Functions for interacting with the events table in the database
#
# Tony Mack <tmack@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: Events.py,v 1.4 2006/10/31 21:46:14 mlhuang Exp $
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
        'event_type': Parameter(str, "Type of event"),
        'object_type': Parameter(str, "Type of object affected by this event"),
        'fault_code': Parameter(int, "Event fault code"),
        'call': Parameter(str, "Call responsible for this event"),
        'runtime': Parameter(float, "Runtime of event"),
        'time': Parameter(int, "Date and time that the event took place, in seconds since UNIX epoch", ro = True),
        'object_ids': Parameter([int], "IDs of objects affected by this event")
	}    

    def add_object(self, object_id, commit = True):
        """
        Relate object to this event.
        """

        assert 'event_id' in self

        event_id = self['event_id']

        if 'object_ids' not in self:
            self['object_ids'] = []

        if object_id not in self['object_ids']:
            self.api.db.do("INSERT INTO event_object (event_id, object_id)" \
                           " VALUES(%(event_id)d, %(object_id)d)",
                           locals())

            if commit:
                self.api.db.commit()

            self['object_ids'].append(object_id)
    
class Events(Table):
    """
    Representation of row(s) from the events table in the database. 
    """

    def __init__(self, api, event_filter):
        Table.__init__(self, api, Event)

        sql = "SELECT %s FROM view_events WHERE True" % \
              ", ".join(Event.fields)

        if event_filter is not None:
            if isinstance(event_filter, list):
                event_filter = Filter(Event.fields, {'event_id': event_filter})
            elif isinstance(event_filter, dict):
                event_filter = Filter(Event.fields, event_filter)
            sql += " AND (%s)" % event_filter.sql(api)

        self.selectall(sql)
