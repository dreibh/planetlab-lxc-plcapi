from types import StringTypes
import random
import base64
import time

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Debug import profile
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

    add_person = Row.add_object(Person, 'person_session')

    def add_node(self, node, commit = True):
        # Nodes can have only one session at a time
        self.api.db.do("DELETE FROM node_session WHERE node_id = %d" % \
                       node['node_id'])

        add = Row.add_object(Node, 'node_session')
        add(self, node, commit = commit)

    def sync(self, commit = True, insert = None):
        if not self.has_key('session_id'):
            # Before a new session is added, delete expired sessions
            expired = Sessions(self.api, expires = -int(time.time()))
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

    def __init__(self, api, session_filter = None, expires = int(time.time())):
        Table.__init__(self, api, Session)

        sql = "SELECT %s FROM view_sessions WHERE True" % \
              ", ".join(Session.fields)

        if session_filter is not None:
            if isinstance(session_filter, (list, tuple, set)):
                # Separate the list into integers and strings
                ints = filter(lambda x: isinstance(x, (int, long)), session_filter)
                strs = filter(lambda x: isinstance(x, StringTypes), session_filter)
                session_filter = Filter(Session.fields, {'person_id': ints, 'session_id': strs})
                sql += " AND (%s) %s" % session_filter.sql(api, "OR")
            elif isinstance(session_filter, dict):
                session_filter = Filter(Session.fields, session_filter)
                sql += " AND (%s) %s" % session_filter.sql(api, "AND")
            elif isinstance(session_filter, (int, long)):
                session_filter = Filter(Session.fields, {'person_id': session_filter})
                sql += " AND (%s) %s" % session_filter.sql(api, "AND")
            elif isinstance(session_filter, StringTypes):
                session_filter = Filter(Session.fields, {'session_id': session_filter})
                sql += " AND (%s) %s" % session_filter.sql(api, "AND")
            else:
                raise PLCInvalidArgument, "Wrong session filter"%session_filter

        if expires is not None:
            if expires >= 0:
                sql += " AND expires > %(expires)d"
            else:
                expires = -expires
                sql += " AND expires < %(expires)d"

        self.selectall(sql, locals())
