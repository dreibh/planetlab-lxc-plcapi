#
# Functions for interacting with the roles table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: Roles.py,v 1.1 2006/09/06 15:36:07 mlhuang Exp $
#

class Roles(dict):
    """
    Representation of the roles table in the database.
    """

    # Role IDs equal to or lower than this number are for use by real
    # accounts. Other role IDs are used internally.
    role_max = 500

    def __init__(self, api):
        sql = "SELECT * FROM roles" \
              " WHERE role_id <= %d" % self.role_max

        for row in api.db.selectall(sql):
            self[row['role_id']] = row['name']
            self[row['name']] = row['role_id']
