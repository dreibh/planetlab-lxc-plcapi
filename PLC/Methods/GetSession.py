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
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node']
    accepts = [Auth()]
    returns = Session.fields['session_id']
    

    def call(self, auth):
        # Authenticated with a session key, just return it
        if auth.has_key('session'):
            return auth['session']

        session = Session(self.api)

        if isinstance(self.caller, Person):
            # XXX Make this configurable
            session['expires'] = int(time.time()) + (24 * 60 * 60)

        session.sync(commit = False)

        if isinstance(self.caller, Node):
            session.add_node(self.caller, commit = True)
        elif isinstance(self.caller, Person):
            session.add_person(self.caller, commit = True)

        return session['session_id']
