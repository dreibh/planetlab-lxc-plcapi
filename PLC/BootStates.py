#
# Functions for interacting with the node_bootstates table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: BootStates.py,v 1.1 2006/09/06 15:36:06 mlhuang Exp $
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
        sql = "SELECT * FROM boot_states"
        
        for row in api.db.selectall(sql):
            self.append(row['boot_state'])
