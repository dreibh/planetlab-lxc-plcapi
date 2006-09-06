#
# Functions for interacting with the node_bootstates table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id$
#

from PLC.Parameter import Parameter

class BootStates(list):
    """
    Representation of the node_bootstates table in the database.
    """

    fields = {
        'boot_state': Parameter(int, "Node boot state"),
        }

    def __init__(self, api):
        sql = "SELECT * FROM node_bootstates"
        
        for row in api.db.selectall(sql):
            self.append(row['boot_state'])
