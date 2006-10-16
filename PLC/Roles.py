#
# Functions for interacting with the roles table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: Roles.py,v 1.3 2006/10/10 21:54:59 mlhuang Exp $
#

from types import StringTypes
from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Table import Row, Table

class Role(Row):
    """
    Representation of a row in the roles table. To use,
    instantiate with a dict of values.
    """

    table_name = 'roles'
    primary_key = 'role_id'
    fields = {
        'role_id': Parameter(int, "Role identifier"),
        'name': Parameter(str, "Role", max = 100),
        }

    def __init__(self, api, fields = {}):
        Row.__init__(self, fields)
        self.api = api

    def validate_role_id(self, role_id):
	# Make sure role does not already exist
	conflicts = Roles(self.api, [role_id])
        if conflicts:
            raise PLCInvalidArgument, "Role ID already in use"

        return role_id

    def validate_name(self, name):
	# Remove leading and trailing spaces
	name = name.strip()

	# Make sure name is not blank after we removed the spaces
        if not name:
            raise PLCInvalidArgument, "Role must be specified"
	
	# Make sure role does not already exist
	conflicts = Roles(self.api, [name])
        if conflicts:
            raise PLCInvalidArgument, "Role name already in use"

	return name

    def delete(self, commit = True):
        assert 'role_id' in self

        # Clean up miscellaneous join tables
        for table in ['person_role', 'roles']:
            self.api.db.do("DELETE FROM %s" \
                           " WHERE role_id = %d" % \
                           (table, self['role_id']), self)

        self.api.db.do("DELETE FROM slice_attribute_types WHERE min_role_id = %d" % \
                       self['role_id'])

        if commit:
            self.api.db.commit()
        
class Roles(Table):
    """
    Representation of the roles table in the database.
    """

    def __init__(self, api, role_id_or_name_list = None):
        sql = "SELECT %s FROM roles" % \
              ", ".join(Role.fields)
        
        if role_id_or_name_list:
            # Separate the list into integers and strings
            role_ids = filter(lambda role_id: isinstance(role_id, (int, long)),
                                   role_id_or_name_list)
            names = filter(lambda name: isinstance(name, StringTypes),
                           role_id_or_name_list)
            sql += " WHERE (False"
            if role_ids:
                sql += " OR role_id IN (%s)" % ", ".join(map(str, role_ids))
            if names:
                sql += " OR name IN (%s)" % ", ".join(api.db.quote(names))
            sql += ")"

        rows = api.db.selectall(sql)

        for row in rows:
            self[row['role_id']] = Role(api, row)
