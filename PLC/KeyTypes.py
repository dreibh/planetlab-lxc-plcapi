#
# Functions for interacting with the key_types table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Table import Row, Table

class KeyType(Row):
    """
    Representation of a row in the key_types table. To use,
    instantiate with a dict of values.
    """

    table_name = 'key_types'
    primary_key = 'key_type'
    join_tables = ['keys']
    fields = {
        'key_type': Parameter(str, "Key type", max = 20),
        }

    def validate_key_type(self, name):
        # Make sure name is not blank
        if not len(name):
            raise PLCInvalidArgument, "Key type must be specified"

        # Make sure key type does not alredy exist
        conflicts = KeyTypes(self.api, [name])
        if conflicts:
            raise PLCInvalidArgument, "Key type name already in use"

        return name

class KeyTypes(Table):
    """
    Representation of the key_types table in the database.
    """

    def __init__(self, api, key_types = None):
        Table.__init__(self, api, KeyType)

        sql = "SELECT %s FROM key_types" % \
              ", ".join(KeyType.fields)

        if key_types:
            sql += " WHERE key_type IN (%s)" % ", ".join( [ api.db.quote (t) for t in key_types ] )

        self.selectall(sql)
