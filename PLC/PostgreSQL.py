#
# PostgreSQL database interface.
# Sort of like DBI(3) (Database independent interface for Perl).
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# pylint: disable=c0103, c0111

import subprocess
import re
from pprint import pformat
from datetime import datetime as DateTimeType

import psycopg2
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
# UNICODEARRAY not exported yet
psycopg2.extensions.register_type(psycopg2._psycopg.UNICODEARRAY)

from PLC.Logger import logger
#from PLC.Debug import profile
from PLC.Faults import *

class PostgreSQL:
    def __init__(self, api):
        self.api = api
        self.debug = False
#        self.debug = True
        self.connection = None

    def cursor(self):
        if self.connection is None:
            # (Re)initialize database connection
            try:
                # Try UNIX socket first
                self.connection = psycopg2.connect(
                    user=self.api.config.PLC_DB_USER,
                    password=self.api.config.PLC_DB_PASSWORD,
                    database=self.api.config.PLC_DB_NAME)
            except psycopg2.OperationalError:
                # Fall back on TCP
                self.connection = psycopg2.connect(
                    user=self.api.config.PLC_DB_USER,
                    password=self.api.config.PLC_DB_PASSWORD,
                    database=self.api.config.PLC_DB_NAME,
                    host=self.api.config.PLC_DB_HOST,
                    port=self.api.config.PLC_DB_PORT)
            self.connection.set_client_encoding("UNICODE")

        (self.rowcount, self.description, self.lastrowid) = \
                        (None, None, None)

        return self.connection.cursor()

    def close(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    @staticmethod
    # From pgdb, and simplify code
    # this is **very different** from the python2 code !
    def _quote(x):
        if isinstance(x, DateTimeType):
            x = str(x)
        elif isinstance(x, bytes):
            x = x.decode('utf-8')

        if isinstance(x, str):
        # don't double quote backslahes, this causes failure
        # with e.g. the SFA code when it tries to spot slices
        # created from fed4fire, which to my knowledge is the only
        # place where a backslash is useful
        #    x = x.replace("\\", "\\\\")
            x = x.replace("'", "''")
            x = f"'{x}'"
        elif isinstance(x, (int, float)):
            pass
        elif x is None:
            x = 'NULL'
        elif isinstance(x, (list, tuple, set)):
            x = 'ARRAY[%s]' % ', '.join([str(PostgreSQL._quote(x)) for x in x])
        elif hasattr(x, '__pg_repr__'):
            x = x.__pg_repr__()
        else:
            raise PLCDBError('Cannot quote type %s' % type(x))
        return x


    def quote(self, value):
        """
        Returns quoted version of the specified value.
        """
        return PostgreSQL._quote(value)

# following is an unsuccessful attempt to re-use lib code as much as possible
#    def quote(self, value):
#        # The pgdb._quote function is good enough for general SQL
#        # quoting, except for array types.
#        if isinstance (value, (types.ListType, types.TupleType, set)):
#            'ARRAY[%s]' % ', '.join( [ str(self.quote(x)) for x in value ] )
#        else:
#            try:
#                # up to PyGreSQL-3.x, function was pgdb._quote
#                import pgdb
#                return pgdb._quote(value)
#            except:
#                # with PyGreSQL-4.x, use psycopg2's adapt
#                from psycopg2.extensions import adapt
#                return adapt (value)

    @classmethod
    def param(cls, name, value):
        # None is converted to the unquoted string NULL
        if isinstance(value, type(None)):
            conversion = "s"
        # True and False are also converted to unquoted strings
        elif isinstance(value, bool):
            conversion = "s"
        elif isinstance(value, float):
            conversion = "f"
        elif not isinstance(value, str):
            conversion = "d"
        else:
            conversion = "s"

        return '%(' + name + ')' + conversion

    def begin_work(self):
        # Implicit in pgdb.connect()
        pass

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def do(self, query, params=None):
        cursor = self.execute(query, params)
        cursor.close()
        return self.rowcount

    def next_id(self, table_name, primary_key):
        sequence = "{}_{}_seq".format(table_name, primary_key)
        sql = "SELECT nextval('{}')".format(sequence)
        rows = self.selectall(sql, hashref=False)
        if rows:
            return rows[0][0]
        return None

    def last_insert_id(self, table_name, primary_key):
        if isinstance(self.lastrowid, int):
            sql = "SELECT %s FROM %s WHERE oid = %d" % \
                  (primary_key, table_name, self.lastrowid)
            rows = self.selectall(sql, hashref=False)
            if rows:
                return rows[0][0]

        return None

    # modified for psycopg2-2.0.7
    # executemany is undefined for SELECT's
    # see http://www.python.org/dev/peps/pep-0249/
    # accepts either None, a single dict, a tuple of single dict - in which case it execute's
    # or a tuple of several dicts, in which case it executemany's
    def execute(self, query, params=None):

        cursor = self.cursor()
        try:

            # psycopg2 requires %()s format for all parameters,
            # regardless of type.
            # this needs to be done carefully though as with pattern-based filters
            # we might have percents embedded in the query
            # so e.g. GetPersons({'email':'*fake*'}) was resulting in .. LIKE '%sake%'
            if psycopg2:
                query = re.sub(r'(%\([^)]*\)|%)[df]', r'\1s', query)
            # rewrite wildcards set by Filter.py as '***' into '%'
            query = query.replace('***', '%')

            if not params:
                if self.debug:
                    logger.debug('execute0: {}'.format(query))
                cursor.execute(query)
            elif isinstance(params, dict):
                if self.debug:
                    logger.debug('execute-dict: params {} query {}'
                                 .format(params, query%params))
                cursor.execute(query, params)
            elif isinstance(params, tuple) and len(params) == 1:
                if self.debug:
                    logger.debug('execute-tuple {}'.format(query%params[0]))
                cursor.execute(query, params[0])
            else:
                param_seq = (params,)
                if self.debug:
                    for params in param_seq:
                        logger.debug('executemany {}'.format(query%params))
                cursor.executemany(query, param_seq)
            (self.rowcount, self.description, self.lastrowid) = \
                            (cursor.rowcount, cursor.description, cursor.lastrowid)
        except Exception as e:
            try:
                self.rollback()
            except:
                pass
            uuid = subprocess.getoutput("uuidgen")
            message = "Database error {}: - Query {} - Params {}".format(uuid, query, pformat(params))
            logger.exception(message)
            raise PLCDBError("Please contact " + \
                             self.api.config.PLC_NAME + " Support " + \
                             "<" + self.api.config.PLC_MAIL_SUPPORT_ADDRESS + ">" + \
                             " and reference " + uuid)

        return cursor

    def selectall(self, query, params=None, hashref=True, key_field=None):
        """
        Return each row as a dictionary keyed on field name (like DBI
        selectrow_hashref()). If key_field is specified, return rows
        as a dictionary keyed on the specified field (like DBI
        selectall_hashref()).

        If params is specified, the specified parameters will be bound
        to the query.
        """

        cursor = self.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        self.commit()
        if hashref or key_field is not None:
            # Return each row as a dictionary keyed on field name
            # (like DBI selectrow_hashref()).
            labels = [column[0] for column in self.description]
            rows = [dict(list(zip(labels, row))) for row in rows]

        if key_field is not None and key_field in labels:
            # Return rows as a dictionary keyed on the specified field
            # (like DBI selectall_hashref()).
            return {row[key_field]: row for row in rows}
        else:
            return rows

    def fields(self, table, notnull=None, hasdef=None):
        """
        Return the names of the fields of the specified table.
        """

        if hasattr(self, 'fields_cache'):
            if (table, notnull, hasdef) in self.fields_cache:
                return self.fields_cache[(table, notnull, hasdef)]
        else:
            self.fields_cache = {}

        sql = "SELECT attname FROM pg_attribute, pg_class" \
              " WHERE pg_class.oid = attrelid" \
              " AND attnum > 0 AND relname = %(table)s"

        if notnull is not None:
            sql += " AND attnotnull is %(notnull)s"

        if hasdef is not None:
            sql += " AND atthasdef is %(hasdef)s"

        rows = self.selectall(sql, locals(), hashref=False)

        self.fields_cache[(table, notnull, hasdef)] = [row[0] for row in rows]

        return self.fields_cache[(table, notnull, hasdef)]
