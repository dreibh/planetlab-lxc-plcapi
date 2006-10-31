#
# Functions for interacting with the events table in the database
#
# Tony Mack <tmack@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id$
#

from PLC.Faults import *
from PLC.Parameter import Parameter
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
        'time': Parameter(int, "Date and time that the event took place, in seconds since UNIX epoch"),
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

    def __init__(self, api,
                 event_ids = None,
                 person_ids = None, node_ids = None,
                 event_types = None,
                 object_types = None, object_ids = None,
                 fault_codes = None):
        self.api = api
    
        sql = "SELECT %s from view_events WHERE True" % \
              ", ".join(Event.fields)
        
        if event_ids:
            sql += " AND event_id IN (%s)" % ", ".join(map(str, event_ids))

        if person_ids:
            sql += " AND person_id IN (%s)" % ", ".join(map(str, person_ids))

        if node_ids:
            sql += " AND node_id IN (%s)" % ", ".join(map(str, node_ids))

        if object_ids:
            sql += " AND object_ids in (%s)" % ", ".join(map(str, object_ids))    

        if event_types:
            sql += " AND event_type in (%s)" % ", ".join(api.db.quote(event_types))

        if object_types:
            sql += " AND object_type in (%s)" % ", ".join(api.db.quote(object_types))
        
        if fault_codes:
            sql += " And fault_code in (%s)" % ", ".join(map(str, fault_codes))
    
        rows = self.api.db.selectall(sql)
    
        for row in rows:
            self[row['event_id']] = event = Event(api, row)
            for aggregate in ['object_ids']:
                if not event.has_key(aggregate) or event[aggregate] is None:
                    event[aggregate] = []
                else:
                    elements = event[aggregate].split(',')
                    try:
                        event[aggregate] = map(int, elements)
                    except ValueError:
                        event[aggregate] = elements
