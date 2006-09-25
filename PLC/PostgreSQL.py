#
# PostgreSQL database interface. Sort of like DBI(3) (Database
# independent interface for Perl).
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: PostgreSQL.py,v 1.1 2006/09/06 15:36:07 mlhuang Exp $
#

import pgdb
from types import StringTypes, NoneType
import traceback
import commands
from pprint import pformat

from PLC.Debug import profile, log
from PLC.Faults import *

class PostgreSQL:
    def __init__(self, api):
        self.api = api

        # Initialize database connection
        self.db = pgdb.connect(user = api.config.PLC_DB_USER,
                               password = api.config.PLC_DB_PASSWORD,
                               host = "%s:%d" % (api.config.PLC_DB_HOST, api.config.PLC_DB_PORT),
                               database = api.config.PLC_DB_NAME)
        self.cursor = self.db.cursor()

        (self.rowcount, self.description, self.lastrowid) = \
                        (None, None, None)

    def quote(self, params):
        """
        Returns quoted version(s) of the specified parameter(s).
        """

        # pgdb._quote functions are good enough for general SQL quoting
        if hasattr(params, 'has_key'):
            params = pgdb._quoteitem(params)
        elif isinstance(params, list) or isinstance(params, tuple):
            params = map(pgdb._quote, params)
        else:
            params = pgdb._quote(params)

        return params

    quote = classmethod(quote)

    def param(self, name, value):
        # None is converted to the unquoted string NULL
        if isinstance(value, NoneType):
            conversion = "s"
        # True and False are also converted to unquoted strings
        elif isinstance(value, bool):
            conversion = "s"
        elif isinstance(value, float):
            conversion = "f"
        elif not isinstance(value, StringTypes):
            conversion = "d"
        else:
            conversion = "s"

        return '%(' + name + ')' + conversion

    param = classmethod(param)

    def begin_work(self):
        # Implicit in pgdb.connect()
        pass

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()

    def do(self, query, params = None):
        self.execute(query, params)
        return self.rowcount

    def last_insert_id(self):
        return self.lastrowid

    def execute(self, query, params = None):
        self.execute_array(query, (params,))

    def execute_array(self, query, param_seq):
        cursor = self.cursor
        try:
            cursor.executemany(query, param_seq)
            (self.rowcount, self.description, self.lastrowid) = \
                            (cursor.rowcount, cursor.description, cursor.lastrowid)
        except pgdb.DatabaseError, e:
            self.rollback()
            uuid = commands.getoutput("uuidgen")
            print >> log, "Database error %s:" % uuid
            print >> log, e
            print >> log, "Query:"
            print >> log, query
            print >> log, "Params:"
            print >> log, pformat(param_seq[0])
            raise PLCDBError("Please contact " + \
                             self.api.config.PLC_NAME + " Support " + \
                             "<" + self.api.config.PLC_MAIL_SUPPORT_ADDRESS + ">" + \
                             " and reference " + uuid)

    def selectall(self, query, params = None, hashref = True, key_field = None):
        """
        Return each row as a dictionary keyed on field name (like DBI
        selectrow_hashref()). If key_field is specified, return rows
        as a dictionary keyed on the specified field (like DBI
        selectall_hashref()).

        If params is specified, the specified parameters will be bound
        to the query (see PLC.DB.parameterize() and
        pgdb.cursor.execute()).
        """

        self.execute(query, params)
        rows = self.cursor.fetchall()

        if hashref:
            # Return each row as a dictionary keyed on field name
            # (like DBI selectrow_hashref()).
            labels = [column[0] for column in self.description]
            rows = [dict(zip(labels, row)) for row in rows]

        if key_field is not None and key_field in labels:
            # Return rows as a dictionary keyed on the specified field
            # (like DBI selectall_hashref()).
            return dict([(row[key_field], row) for row in rows])
        else:
            return rows

    def fields(self, table):
        """
        Return the names of the fields of the specified table.
        """

        rows = self.selectall("SELECT attname FROM pg_attribute, pg_class" \
                              " WHERE pg_class.oid = attrelid" \
                              " AND attnum > 0 AND relname = %(table)s",
                              locals(),
                              hashref = False)

        return [row[0] for row in rows]
