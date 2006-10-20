#
# Functions for interacting with the network_types table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: NetworkTypes.py,v 1.1 2006/10/10 20:24:06 mlhuang Exp $
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
    join_tables = ['nodenetworks']
    fields = {
        'type': Parameter(str, "Network type", max = 20),
        }

    def validate_type(self, name):
	# Remove leading and trailing spaces
	name = name.strip()

	# Make sure name is not blank after we removed the spaces
        if not name:
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

    def __init__(self, api, names = None):
        sql = "SELECT %s FROM network_types" % \
              ", ".join(NetworkType.fields)
        
        if names:
            # Separate the list into integers and strings
            sql += " WHERE type IN (%s)" % ", ".join(api.db.quote(names))

        rows = api.db.selectall(sql)

        for row in rows:
            self[row['type']] = NetworkType(api, row)
