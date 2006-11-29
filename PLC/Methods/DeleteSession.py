import time

from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import SessionAuth
from PLC.Sessions import Session, Sessions

class DeleteSession(Method):
    """
    Invalidates the current session.

    Returns 1 if successful.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node']
    accepts = [SessionAuth()]
    returns = Parameter(int, '1 if successful')


    def call(self, auth):
        assert auth.has_key('session')

        sessions = Sessions(self.api, [auth['session']])
        if not sessions:
            raise PLCAPIError, "No such session"
        session = sessions[0]

        session.delete()

        return 1
