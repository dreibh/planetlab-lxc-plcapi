#
# Functions for interacting with the events table in the database
#
# Tony Mack <tmack@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: EventObjects.py,v 1.1 2007/02/27 18:54:32 tmack Exp $
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
	
	# Since we are querying a table (not a view) ensure that timestamps
	# are converted to ints in the db before being returned
	timestamps = ['time']
	for col in self.columns:
	    if col in timestamps:
	        if isinstance(self.columns, (list, tuple, set)): 
		    index = self.columns.index(col)
	            self.columns[index] = "CAST(date_part('epoch', events.time) AS bigint) AS time"
		elif isinstance(self.columns, dict):
		    type = self.columns.pop(col)
		    self.columns["CAST(date_part('epoch', events.time) AS bigint) AS time"] = type
	    elif col in [EventObject.primary_key]:
	       	if isinstance(self.columns, (list, tuple, set)):
                    index = self.columns.index(col)
                    self.columns[index] = EventObject.table_name+"."+EventObject.primary_key
                elif isinstance(self.columns, dict):
                    type = self.columns.pop(col)
                    self.columns[EventObject.table_name+"."+EventObject.primary_key] = type
			 
	sql = "SELECT %s FROM event_object, events WHERE True" % \
            ", ".join(self.columns)
        
	if event_filter is not None:
            if isinstance(event_filter, (list, tuple, set)):
                event_filter = Filter(EventObject.fields, {'event_id': event_filter})
            elif isinstance(event_filter, dict):
                event_filter = Filter(EventObject.fields, event_filter)
            sql += " AND (%s) " % event_filter.sql(api)
	sql += " AND events.event_id = event_object.event_id " 
	sql += " ORDER BY %s" % EventObject.table_name+"."+EventObject.primary_key
        
	self.selectall(sql)
