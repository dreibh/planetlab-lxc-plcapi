#
# Functions for interacting with the key_types table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: KeyTypes.py,v 1.1 2006/10/10 20:24:06 mlhuang Exp $
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
    fields = {
        'key_type': Parameter(str, "Key type", max = 20),
        }

    def __init__(self, api, fields = {}):
        Row.__init__(self, fields)
        self.api = api

    def validate_key_type(self, name):
	# Remove leading and trailing spaces
	name = name.strip()

	# Make sure name is not blank after we removed the spaces
        if not name:
            raise PLCInvalidArgument, "Key type must be specified"
	
	# Make sure key type does not alredy exist
	conflicts = KeyTypes(self.api, [name])
        if conflicts:
            raise PLCInvalidArgument, "Key type name already in use"

	return name

    def delete(self, commit = True):
        assert 'key_type' in self

        # Clean up miscellaneous join tables
        for table in ['keys', 'key_types']:
            self.api.db.do("DELETE FROM " + table + \
                           " WHERE key_type = %(key_type)s",
                           self)

        if commit:
            self.api.db.commit()
        
class KeyTypes(Table):
    """
    Representation of the key_types table in the database.
    """

    def __init__(self, api, names = None):
        sql = "SELECT %s FROM key_types" % \
              ", ".join(KeyType.fields)
        
        if names:
            # Separate the list into integers and strings
            sql += " WHERE key_type IN (%s)" % ", ".join(api.db.quote(names))

        rows = api.db.selectall(sql)

        for row in rows:
            self[row['key_type']] = KeyType(api, row)
