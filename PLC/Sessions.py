import random
import base64
import time

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Table import Row, Table
from PLC.Persons import Person, Persons
from PLC.Nodes import Node, Nodes

class Session(Row):
    """
    Representation of a row in the sessions table. To use, instantiate
    with a dict of values.
    """

    table_name = 'sessions'
    primary_key = 'session_id'
    join_tables = ['person_session', 'node_session']
    fields = {
        'session_id': Parameter(str, "Session key"),
        'person_id': Parameter(int, "Account identifier, if applicable"),
        'node_id': Parameter(int, "Node identifier, if applicable"),
        'expires': Parameter(int, "Date and time when session expires, in seconds since UNIX epoch"),
        }

    def validate_expires(self, expires):
        if expires < time.time():
            raise PLCInvalidArgument, "Expiration date must be in the future"

        return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(expires))

    def add_person(self, person, commit = True):
        """
        Associate person with session.
        """

        assert 'session_id' in self
        assert isinstance(person, Person)
        assert 'person_id' in person

        session_id = self['session_id']
        person_id = person['person_id']

        self.api.db.do("INSERT INTO person_session (session_id, person_id)" \
                       " VALUES(%(session_id)s, %(person_id)d)",
                       locals())

        if commit:
            self.api.db.commit()

        self['person_id'] = person_id

    def add_node(self, node, commit = True):
        """
        Associate node with session.
        """

        assert 'session_id' in self
        assert isinstance(node, Node)
        assert 'node_id' in node

        session_id = self['session_id']
        node_id = node['node_id']

        # Nodes can have only one session at a time
        self.api.db.do("DELETE FROM node_session WHERE node_id = %(node_id)d",
                       locals())

        self.api.db.do("INSERT INTO node_session (session_id, node_id)" \
                       " VALUES(%(session_id)s, %(node_id)d)",
                       locals())

        if commit:
            self.api.db.commit()

        self['node_id'] = node_id

    def sync(self, commit = True, insert = None):
        if not self.has_key('session_id'):
            # Before a new session is added, delete expired sessions
            expired = Sessions(self.api, expires = -int(time.time())).values()
            for session in expired:
                session.delete(commit)

            # Generate 32 random bytes
            bytes = random.sample(xrange(0, 256), 32)
            # Base64 encode their string representation
            self['session_id'] = base64.b64encode("".join(map(chr, bytes)))
            # Force insert
            insert = True

        Row.sync(self, commit, insert)

class Sessions(Table):
    """
    Representation of row(s) from the session table in the database.
    """

    def __init__(self, api, session_ids = None, expires = int(time.time())):
	Table.__init__(self, api, Session)

        sql = "SELECT %s FROM view_sessions WHERE True" % \
              ", ".join(Session.fields)

        if session_ids:
            sql += " AND session_id IN (%s)" % ", ".join(map(api.db.quote, session_ids))

        if expires is not None:
            if expires >= 0:
                sql += " AND expires > %(expires)d"
            else:
                expires = -expires
                sql += " AND expires < %(expires)d"

        self.selectall(sql, locals())
