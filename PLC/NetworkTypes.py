#
# Functions for interacting with the network_types table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Table import Row, Table

class NetworkType(Row):
    """
    Representation of a row in the network_types table. To use,
    instantiate with a dict of values.
    """

    table_name = 'network_types'
    primary_key = 'type'
    join_tables = ['interfaces']
    fields = {
        'type': Parameter(str, "Network type", max = 20),
        }

    def validate_type(self, name):
        # Make sure name is not blank
        if not len(name):
            raise PLCInvalidArgument, "Network type must be specified"

        # Make sure network type does not alredy exist
        conflicts = NetworkTypes(self.api, [name])
        if conflicts:
            raise PLCInvalidArgument, "Network type name already in use"

        return name

class NetworkTypes(Table):
    """
    Representation of the network_types table in the database.
    """

    def __init__(self, api, types = None):
        Table.__init__(self, api, NetworkType)

        sql = "SELECT %s FROM network_types" % \
              ", ".join(NetworkType.fields)

        if types:
            sql += " WHERE type IN (%s)" % ", ".join( [ api.db.quote (t) for t in types ] )

        self.selectall(sql)
