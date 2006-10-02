#
# Functions for interacting with the node_bootstates table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: BootStates.py,v 1.2 2006/09/25 14:48:07 mlhuang Exp $
#

class BootStates(list):
    """
    Representation of the node_bootstates table in the database.
    """

    def __init__(self, api):
        sql = "SELECT * FROM boot_states"
        
        for row in api.db.selectall(sql):
            self.append(row['boot_state'])
