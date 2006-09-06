#
# Functions for interacting with the roles table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id$
#

from PLC.Parameter import Parameter

class Roles(dict):
    """
    Representation of the roles table in the database.
    """

    fields = {
        'role_id': Parameter(int, "Role identifier"),
        'name': Parameter(str, "Role name"),
        }

    # Role IDs equal to or lower than this number are for use by real
    # accounts. Other role IDs are used internally.
    role_max = 500

    def __init__(self, api):
        sql = "SELECT * FROM roles" \
              " WHERE role_id <= %d" % self.role_max

        for row in api.db.selectall(sql):
            self[row['role_id']] = row['name']
            self[row['name']] = row['role_id']
