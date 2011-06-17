import time

from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth
from PLC.Sessions import Session, Sessions
from PLC.Nodes import Node, Nodes
from PLC.Persons import Person, Persons

class GetSession(Method):
    """
    Returns a new session key if a user or node authenticated
    successfully, faults otherwise.

    Default value for 'expires' is 24 hours.  Otherwise, the returned 
    session 'expires' in the given number of seconds.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node']
    accepts = [Auth(),
               Parameter(int,"expires", nullok=True)]
    returns = Session.fields['session_id']


    def call(self, auth, expires=None):
        # Authenticated with a session key, just return it
        if auth.has_key('session'):
            return auth['session']

        session = Session(self.api)

        if isinstance(self.caller, Person):
            # XXX Make this configurable
            if expires is None:
                session['expires'] = int(time.time()) + (24 * 60 * 60)
            else:
                session['expires'] = int(time.time()) + int(expires)

        session.sync(commit = False)

        if isinstance(self.caller, Node):
            session.add_node(self.caller, commit = True)
        elif isinstance(self.caller, Person):
            session.add_person(self.caller, commit = True)

        return session['session_id']
