#
# Functions for interacting with the boot_states table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Table import Row, Table

class BootState(Row):
    """
    Representation of a row in the boot_states table. To use,
    instantiate with a dict of values.
    """

    table_name = 'boot_states'
    primary_key = 'boot_state'
    join_tables = ['nodes']
    fields = {
        'boot_state': Parameter(str, "Boot state", max = 20),
        }

    def validate_boot_state(self, name):
        # Make sure name is not blank
        if not len(name):
            raise PLCInvalidArgument, "Boot state must be specified"

        # Make sure boot state does not alredy exist
        conflicts = BootStates(self.api, [name])
        if conflicts:
            raise PLCInvalidArgument, "Boot state name already in use"

        return name

class BootStates(Table):
    """
    Representation of the boot_states table in the database.
    """

    def __init__(self, api, boot_states = None):
        Table.__init__(self, api, BootState)

        sql = "SELECT %s FROM boot_states" % \
              ", ".join(BootState.fields)

        if boot_states:
            sql += " WHERE boot_state IN (%s)" % ", ".join( [ api.db.quote (s) for s in boot_states ] )

        self.selectall(sql)
