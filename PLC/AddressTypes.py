#
# Functions for interacting with the address_types table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#

from types import StringTypes
from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
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
        'name': Parameter(str, "Address type", max = 20),
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

    def __init__(self, api, address_type_filter = None, columns = None):
        Table.__init__(self, api, AddressType, columns)

        sql = "SELECT %s FROM address_types WHERE True" % \
              ", ".join(self.columns)

        if address_type_filter is not None:
            if isinstance(address_type_filter, (list, tuple, set)):
                # Separate the list into integers and strings
                ints = filter(lambda x: isinstance(x, (int, long)), address_type_filter)
                strs = filter(lambda x: isinstance(x, StringTypes), address_type_filter)
                address_type_filter = Filter(AddressType.fields, {'address_type_id': ints, 'name': strs})
                sql += " AND (%s) %s" % address_type_filter.sql(api, "OR")
            elif isinstance(address_type_filter, dict):
                address_type_filter = Filter(AddressType.fields, address_type_filter)
                sql += " AND (%s) %s" % address_type_filter.sql(api, "AND")
            elif isinstance(address_type_filter, (int, long)):
                address_type_filter = Filter(AddressType.fields, {'address_type_id': address_type_filter})
                sql += " AND (%s) %s" % address_type_filter.sql(api, "AND")
            elif isinstance(address_type_filter, StringTypes):
                address_type_filter = Filter(AddressType.fields, {'name': address_type_filter})
                sql += " AND (%s) %s" % address_type_filter.sql(api, "AND")
            else:
                raise PLCInvalidArgument, "Wrong address type filter %r"%address_type_filter

        self.selectall(sql)
