#
# Functions for interacting with the roles table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#

from types import StringTypes
from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Table import Row, Table

class Role(Row):
    """
    Representation of a row in the roles table. To use,
    instantiate with a dict of values.
    """

    table_name = 'roles'
    primary_key = 'role_id'
    join_tables = ['person_role', 'tag_type_role' ]
    fields = {
        'role_id': Parameter(int, "Role identifier"),
        'name': Parameter(str, "Role", max = 100),
        }

    def validate_role_id(self, role_id):
        # Make sure role does not already exist
        conflicts = Roles(self.api, [role_id])
        if conflicts:
            raise PLCInvalidArgument, "Role ID already in use"

        return role_id

    def validate_name(self, name):
        # Make sure name is not blank
        if not len(name):
            raise PLCInvalidArgument, "Role must be specified"

        # Make sure role does not already exist
        conflicts = Roles(self.api, [name])
        if conflicts:
            raise PLCInvalidArgument, "Role name already in use"

        return name

class Roles(Table):
    """
    Representation of the roles table in the database.
    """

    def __init__(self, api, role_filter = None):
        Table.__init__(self, api, Role)

        sql = "SELECT %s FROM roles WHERE True" % \
              ", ".join(Role.fields)

        if role_filter is not None:
            if isinstance(role_filter, (list, tuple, set)):
                # Separate the list into integers and strings
                ints = filter(lambda x: isinstance(x, (int, long)), role_filter)
                strs = filter(lambda x: isinstance(x, StringTypes), role_filter)
                role_filter = Filter(Role.fields, {'role_id': ints, 'name': strs})
                sql += " AND (%s) %s" % role_filter.sql(api, "OR")
            elif isinstance(role_filter, dict):
                role_filter = Filter(Role.fields, role_filter)
                sql += " AND (%s) %s" % role_filter.sql(api, "AND")
            elif isinstance(role_filter, (int, long)):
                role_filter = Filter(Role.fields, {'role_id': role_filter})
                sql += " AND (%s) %s" % role_filter.sql(api, "AND")
            elif isinstance(role_filter, StringTypes):
                role_filter = Filter(Role.fields, {'name': role_filter})
                sql += " AND (%s) %s" % role_filter.sql(api, "AND")
            else:
                raise PLCInvalidArgument, "Wrong role filter %r"%role_filter

        self.selectall(sql)
