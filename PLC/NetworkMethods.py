#
# Functions for interacting with the network_methods table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: NetworkMethods.py,v 1.3 2006/10/24 20:02:22 mlhuang Exp $
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

    def __init__(self, api, methods = None):
        Table.__init__(self, api, NetworkMethod)

        sql = "SELECT %s FROM network_methods" % \
              ", ".join(NetworkMethod.fields)
        
        if methods:
            sql += " WHERE method IN (%s)" % ", ".join(map(api.db.quote, methods))

        self.selectall(sql)
