from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.EventObjects import EventObject, EventObjects
from PLC.Auth import Auth

class GetEventObjects(Method):
    """
    Returns an array of structs containing details about events and
    faults. If event_filter is specified and is an array of event
    identifiers, or a struct of event attributes, only events matching
    the filter will be returned. If return_fields is specified, only the
    specified details will be returned.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Mixed(Filter(EventObject.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [EventObject.fields]

    def call(self, auth, event_filter = None, return_fields = None):
        return EventObjects(self.api, event_filter, return_fields)
