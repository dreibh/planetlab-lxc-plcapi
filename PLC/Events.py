#
# Functions for interacting with the events table in the database
#
# Tony Mack <tmack@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
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
		'person_id': Parameter(int, "Identifier of person responsible for event"),
		'event_type': Parameter(str, "Type of event"),
		'object_type': Parameter(str, "Type of object affected by this event"),
		'fault_code': Parameter(int, "Event fault code"),
		'call': Parameter(str, "Call responsible for this event"),
		'time': Parameter(str, "Date/Time the event took place"),
		'object_ids': Parameter([int], "Ids of objects affected by this event")
	}	
	
	def __init__(self, api, fields = {}):
		Row.__init__(self, fields)
		self.api = api

	

class Events(Table):
	"""
	Representation of row(s) from the events table in the database. 
	"""

	def __init__(self, api, event_ids = None, person_ids = None, event_types = None, \
		     object_types = None, object_ids = None, fault_codes = None):
	
		self.api = api
			
		sql = "SELECT %s from view_events WHERE True" % ", ".join(Event.fields)
		
		if event_ids:
			sql += " AND event_id IN (%s)" % ", ".join(map(str, event_ids))

		if person_ids:
			sql += " AND person_id IN (%s)" % ", ".join(map(str, person_ids))
		
		if object_ids:
			sql += " AND object_ids in (%s)" % ", ".join(map(str, object_ids))	

		if event_types:
			sql += " AND event_type in (%s)" % ", ".join(api.db.quote(event_types))

		if object_types:
			sql += " AND object_type in (%s)" % ", ".join(api.db.quote(object_types))

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
