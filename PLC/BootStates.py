#
# Functions for interacting with the boot_states table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: BootStates.py,v 1.1 2006/10/10 20:24:06 mlhuang Exp $
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
    fields = {
        'boot_state': Parameter(str, "Boot state", max = 20),
        }

    def __init__(self, api, fields = {}):
        Row.__init__(self, fields)
        self.api = api

    def validate_boot_state(self, name):
	# Remove leading and trailing spaces
	name = name.strip()

	# Make sure name is not blank after we removed the spaces
        if not name:
            raise PLCInvalidArgument, "Boot state must be specified"
	
	# Make sure boot state does not alredy exist
	conflicts = BootStates(self.api, [name])
        if conflicts:
            raise PLCInvalidArgument, "Boot state name already in use"

	return name

    def delete(self, commit = True):
        assert 'boot_state' in self

        # Clean up miscellaneous join tables
        for table in ['nodes', 'boot_states']:
            self.api.db.do("DELETE FROM " + table + \
                           " WHERE boot_state = %(boot_state)s",
                           self)

        if commit:
            self.api.db.commit()
        
class BootStates(Table):
    """
    Representation of the boot_states table in the database.
    """

    def __init__(self, api, names = None):
        sql = "SELECT %s FROM boot_states" % \
              ", ".join(BootState.fields)
        
        if names:
            # Separate the list into integers and strings
            sql += " WHERE boot_state IN (%s)" % ", ".join(api.db.quote(names))

        rows = api.db.selectall(sql)

        for row in rows:
            self[row['boot_state']] = BootState(api, row)
