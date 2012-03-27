#
# Functions for interacting with the initscripts table in the database
#
# Tony Mack <tmack@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#

from types import StringTypes
from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Table import Row, Table

class InitScript(Row):
    """
    Representation of a row in the initscripts table. To use,
    instantiate with a dict of values.
    """

    table_name = 'initscripts'
    primary_key = 'initscript_id'
    join_tables = []
    fields = {
        'initscript_id': Parameter(int, "Initscript identifier"),
        'name': Parameter(str, "Initscript name", max = 254),
        'enabled': Parameter(bool, "Initscript is active"),
        'script': Parameter(str, "Initscript"),
        }

    def validate_name(self, name):
        """
        validates the script name
        """

        conflicts = InitScripts(self.api, [name])
        for initscript in conflicts:
            if 'initscript_id' not in self or self['initscript_id'] != initscript['initscript_id']:
                raise PLCInvalidArgument, "Initscript name already in use"

        return name


class InitScripts(Table):
    """
    Representation of the initscripts table in the database.
    """

    def __init__(self, api, initscript_filter = None, columns = None):
        Table.__init__(self, api, InitScript, columns)

        sql = "SELECT %s FROM initscripts WHERE True" % \
              ", ".join(self.columns)

        if initscript_filter is not None:
            if isinstance(initscript_filter, (list, tuple, set)):
                # Separate the list into integers and strings
                ints = filter(lambda x: isinstance(x, (int, long)), initscript_filter)
                strs = filter(lambda x: isinstance(x, StringTypes), initscript_filter)
                initscript_filter = Filter(InitScript.fields, {'initscript_id': ints, 'name': strs })
                sql += " AND (%s) %s" % initscript_filter.sql(api, "OR")
            elif isinstance(initscript_filter, dict):
                initscript_filter = Filter(InitScript.fields, initscript_filter)
                sql += " AND (%s) %s" % initscript_filter.sql(api, "AND")
            elif isinstance(initscript_filter, (int, long)):
                initscript_filter = Filter(InitScript.fields, {'initscript_id': initscript_filter})
                sql += " AND (%s) %s" % initscript_filter.sql(api, "AND")
            elif isinstance(initscript_filter, StringTypes):
                initscript_filter = Filter(InitScript.fields, {'name': initscript_filter})
                sql += " AND (%s) %s" % initscript_filter.sql(api, "AND")
            else:
                raise PLCInvalidArgument, "Wrong initscript filter %r"%initscript_filter

        self.selectall(sql)
