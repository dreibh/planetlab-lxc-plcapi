#
# Functions for interacting with the address_types table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: AddressTypes.py,v 1.4 2006/10/20 17:43:30 mlhuang Exp $
#

from types import StringTypes
from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Table import Row, Table

class AddressType(Row):
    """
    Representation of a row in the address_types table. To use,
    instantiate with a dict of values.
    """

    table_name = 'address_types'
    primary_key = 'address_type_id'
    join_tables = ['address_address_type']
    fields = {
        'address_type_id': Parameter(int, "Address type identifier"),
        'name': Parameter(str, "Address type", max = 20, optional = False),
        'description': Parameter(str, "Address type description", max = 254),
        }

    def validate_name(self, name):
	# Make sure name is not blank
        if not len(name):
            raise PLCInvalidArgument, "Address type must be specified"
	
	# Make sure address type does not already exist
	conflicts = AddressTypes(self.api, [name])
	for address_type_id in conflicts:
            if 'address_type_id' not in self or self['address_type_id'] != address_type_id:
               raise PLCInvalidArgument, "Address type name already in use"

	return name

class AddressTypes(Table):
    """
    Representation of the address_types table in the database.
    """

    def __init__(self, api, address_type_id_or_name_list = None):
        sql = "SELECT %s FROM address_types" % \
              ", ".join(AddressType.fields)
        
        if address_type_id_or_name_list:
            # Separate the list into integers and strings
            address_type_ids = filter(lambda address_type_id: isinstance(address_type_id, (int, long)),
                                   address_type_id_or_name_list)
            names = filter(lambda name: isinstance(name, StringTypes),
                           address_type_id_or_name_list)
            sql += " WHERE (False"
            if address_type_ids:
                sql += " OR address_type_id IN (%s)" % ", ".join(map(str, address_type_ids))
            if names:
                sql += " OR name IN (%s)" % ", ".join(api.db.quote(names))
            sql += ")"

        rows = api.db.selectall(sql)

        for row in rows:
            self[row['address_type_id']] = AddressType(api, row)
