#
# Functions for interacting with the network_methods table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: NetworkMethods.py,v 1.2 2006/10/20 17:46:02 mlhuang Exp $
#

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Table import Row, Table

class NetworkMethod(Row):
    """
    Representation of a row in the network_methods table. To use,
    instantiate with a dict of values.
    """

    table_name = 'network_methods'
    primary_key = 'method'
    join_tables = ['nodenetworks']
    fields = {
        'method': Parameter(str, "Network method", max = 20),
        }

    def validate_method(self, name):
	# Make sure name is not blank
        if not len(name):
            raise PLCInvalidArgument, "Network method must be specified"
	
	# Make sure network method does not alredy exist
	conflicts = NetworkMethods(self.api, [name])
        if conflicts:
            raise PLCInvalidArgument, "Network method name already in use"

	return name

class NetworkMethods(Table):
    """
    Representation of the network_methods table in the database.
    """

    def __init__(self, api, names = None):
        sql = "SELECT %s FROM network_methods" % \
              ", ".join(NetworkMethod.fields)
        
        if names:
            # Separate the list into integers and strings
            sql += " WHERE method IN (%s)" % ", ".join(api.db.quote(names))

        rows = api.db.selectall(sql)

        for row in rows:
            self[row['method']] = NetworkMethod(api, row)
