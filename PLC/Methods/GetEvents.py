import os

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Events import Event, Events
from PLC.Auth import PasswordAuth

class GetEvents(Method):
    """
    Return an array of dictionaries containing details about the
    specified events.

    if object_ids is specified, and object_types must be specified
    with only 1 object type
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        [Event.fields['event_id']],
	[Event.fields['person_id']],
	Event.fields['object_ids'],
	[Event.fields['event_type']],		
	[Event.fields['object_type']],
	[Event.fields['fault_code']]
        ]

    returns = [Event.fields]

    def __init__(self, *args, **kwds):
        Method.__init__(self, *args, **kwds)
        # Update documentation with list of default fields returned
        self.__doc__ += os.linesep.join(Event.fields.keys())

    def call(self, auth, event_id_list = None, person_id_list = None, event_type_list = None, object_type_list = None, object_id_list = None, fault_code_list = None):
        
	# Authenticated function
      	assert self.caller is not None

	# filter out invalid event types
	if event_type_list:
		valid_event_types = ['Add', 'AddTo', 'Get', 'Update', 'Delete', \
				     'DeleteFrom', 'Unknown']
		if filter(lambda field: field not in valid_event_types, event_type_list):
			raise PLCInvalidArgument, "Invalid event type. Must be in %s" % \
						  valid_event_types
	
	# filter out invalid object types
	if object_type_list:
		valid_object_types = ['AddreessType', 'Address', 'BootState', 'ConfFile', \
				      'KeyType', 'Key', 'NetworkType', 'NodeGroup',\
				      'NodeNetwork', 'Node', 'PCU', 'Perons', 'Site', \
				      'SliceAttributeType', 'SliceAttribute', 'Slice', 'Unknown']
		if filter(lambda field: field not in valid_object_types, object_type_list):
			raise PLCInvalidArgument, "Invalid object type. Must be in %s" % \
						  valid_object_types
	
	# if object ids are specified only 1 object type can be specified
	if object_id_list:
		if not object_type_list:
			raise PLCInvalidArgument, "Object type must be specified"
		elif len(object_type_list) > 1:
			raise PLCInvalidArgument, "Cannot specify multiple object types when object_ids are specified"
	
        # Get node information
        events = Events(self.api, event_id_list, person_id_list, event_type_list, \
		        object_type_list, object_id_list, fault_code_list).values()

        # turn each node into a real dict.
        events = [dict(event) for event in events]
                    
        return events
