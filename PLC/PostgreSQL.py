#
# PostgreSQL database interface. Sort of like DBI(3) (Database
# independent interface for Perl).
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: PostgreSQL.py,v 1.10 2006/11/09 19:34:04 mlhuang Exp $
#

import psycopg2
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
# UNICODEARRAY not exported yet
psycopg2.extensions.register_type(psycopg2._psycopg.UNICODEARRAY)

import pgdb
from types import StringTypes, NoneType
import traceback
import commands
import re
from pprint import pformat

from PLC.Debug import profile, log
from PLC.Faults import *

if not psycopg2:
    is8bit = re.compile("[\x80-\xff]").search

    def unicast(typecast):
        """
        pgdb returns raw UTF-8 strings. This function casts strings that
        appear to contain non-ASCII characters to unicode objects.
        """
    
        def wrapper(*args, **kwds):
            value = typecast(*args, **kwds)

            # pgdb always encodes unicode objects as UTF-8 regardless of
            # the DB encoding (and gives you no option for overriding
            # the encoding), so always decode 8-bit objects as UTF-8.
            if isinstance(value, str) and is8bit(value):
                value = unicode(value, "utf-8")

            return value

        return wrapper

    pgdb.pgdbTypeCache.typecast = unicast(pgdb.pgdbTypeCache.typecast)

class PostgreSQL:
    def __init__(self, api):
        self.api = api

        # Initialize database connection
        if psycopg2:
            try:
                # Try UNIX socket first
                self.db = psycopg2.connect(user = api.config.PLC_DB_USER,
                                           password = api.config.PLC_DB_PASSWORD,
                                           database = api.config.PLC_DB_NAME)
            except psycopg2.OperationalError:
                # Fall back on TCP
                self.db = psycopg2.connect(user = api.config.PLC_DB_USER,
                                           password = api.config.PLC_DB_PASSWORD,
                                           database = api.config.PLC_DB_NAME,
                                           host = api.config.PLC_DB_HOST,
                                           port = api.config.PLC_DB_PORT)
            self.db.set_client_encoding("UNICODE")
        else:
            self.db = pgdb.connect(user = api.config.PLC_DB_USER,
                                   password = api.config.PLC_DB_PASSWORD,
                                   host = "%s:%d" % (api.config.PLC_DB_HOST, api.config.PLC_DB_PORT),
                                   database = api.config.PLC_DB_NAME)

        self.cursor = self.db.cursor()

        (self.rowcount, self.description, self.lastrowid) = \
                        (None, None, None)

    def quote(self, value):
        """
        Returns quoted version of the specified value.
        """

        # The pgdb._quote function is good enough for general SQL
        # quoting, except for array types.
        if isinstance(value, (list, tuple, set)):
            return "ARRAY[%s]" % ", ".join(map, self.quote, value)
        else:
            return pgdb._quote(value)

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

    def last_insert_id(self, table_name, primary_key):
        if isinstance(self.lastrowid, int):
            sql = "SELECT %s FROM %s WHERE oid = %d" % \
                  (primary_key, table_name, self.lastrowid)
            rows = self.selectall(sql, hashref = False)
            if rows:
                return rows[0][0]

        return None

    def execute(self, query, params = None):
        self.execute_array(query, (params,))

    def execute_array(self, query, param_seq):
        cursor = self.cursor
        try:
            # psycopg2 requires %()s format for all parameters,
            # regardless of type.
            if psycopg2:
                query = re.sub(r'(%\([^)]*\)|%)[df]', r'\1s', query)

            cursor.executemany(query, param_seq)
            (self.rowcount, self.description, self.lastrowid) = \
                            (cursor.rowcount, cursor.description, cursor.lastrowid)
        except Exception, e:
            try:
                self.rollback()
            except:
                pass
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

        if hashref or key_field is not None:
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

    def fields(self, table, notnull = None, hasdef = None):
        """
        Return the names of the fields of the specified table.
        """

        sql = "SELECT attname FROM pg_attribute, pg_class" \
              " WHERE pg_class.oid = attrelid" \
              " AND attnum > 0 AND relname = %(table)s"

        if notnull is not None:
            sql += " AND attnotnull is %(notnull)s"

        if hasdef is not None:
            sql += " AND atthasdef is %(hasdef)s"

        rows = self.selectall(sql, locals(), hashref = False)

        return [row[0] for row in rows]
