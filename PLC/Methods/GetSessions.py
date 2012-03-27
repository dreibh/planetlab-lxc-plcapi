from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Sessions import Session, Sessions
from PLC.Persons import Person, Persons
from PLC.Auth import Auth

class GetSessions(Method):
    """
    Returns an array of structs containing details about users sessions. If
    session_filter is specified and is an array of user identifiers or
    session_keys, or a struct of session attributes, only sessions matching the
    filter will be returned. If return_fields is specified, only the
    specified details will be returned.


    """

    roles = ['admin']

    accepts = [
        Auth(),
        Mixed([Mixed(Session.fields['person_id'],
                     Session.fields['session_id'])],
              Filter(Session.fields))
        ]

    returns = [Session.fields]

    def call(self, auth, session_filter = None):

        sessions = Sessions(self.api, session_filter)

        return sessions
