#
# Functions for interacting with the slice_instantiations table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Table import Row, Table

class SliceInstantiation(Row):
    """
    Representation of a row in the slice_instantiations table. To use,
    instantiate with a dict of values.
    """

    table_name = 'slice_instantiations'
    primary_key = 'instantiation'
    join_tables = ['slices']
    fields = {
        'instantiation': Parameter(str, "Slice instantiation state", max = 100),
        }

    def validate_instantiation(self, instantiation):
        # Make sure name is not blank
        if not len(instantiation):
            raise PLCInvalidArgument, "Slice instantiation state name must be specified"

        # Make sure slice instantiation does not alredy exist
        conflicts = SliceInstantiations(self.api, [instantiation])
        if conflicts:
            raise PLCInvalidArgument, "Slice instantiation state name already in use"

        return instantiation

class SliceInstantiations(Table):
    """
    Representation of the slice_instantiations table in the database.
    """

    def __init__(self, api, instantiations = None):
        Table.__init__(self, api, SliceInstantiation)

        sql = "SELECT %s FROM slice_instantiations" % \
              ", ".join(SliceInstantiation.fields)

        if instantiations:
            sql += " WHERE instantiation IN (%s)" % ", ".join( [ api.db.quote (i) for i in instantiations ] )

        self.selectall(sql)
