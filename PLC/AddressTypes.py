#
# Functions for interacting with the address_types table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id$
#

from PLC.Parameter import Parameter

class AddressTypes(dict):
    """
    Representation of the address_types table in the database.
    """

    fields = {
        'address_type_id': Parameter(int, "Address type identifier"),
        'name': Parameter(str, "Address type name"),
        }

    def __init__(self, api):
        sql = "SELECT address_type_id, name FROM address_types"

        for row in api.db.selectall(sql):
            self[row['address_type_id']] = row['name']
            self[row['name']] = row['address_type_id']
