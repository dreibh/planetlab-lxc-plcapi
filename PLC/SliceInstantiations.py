#
# Functions for interacting with the slice_instantiations table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: SliceInstantiations.py,v 1.1 2006/09/06 15:36:07 mlhuang Exp $
#

class SliceInstantiations(list):
    """
    Representation of the slice_instantiations table in the database.
    """

    def __init__(self, api):
        sql = "SELECT * FROM slice_instantiations"

        for row in api.db.selectall(sql):
            self.append[row['instantiation']]
