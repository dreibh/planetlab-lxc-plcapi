from types import StringTypes

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Debug import profile
from PLC.Table import Row, Table

class Slice(Row):
    """
    Representation of a row in the slices table. To use, instantiate
    with a dict of values.
    """

    fields = {
        'slice_id': Parameter(int, "Slice type"),
        }

    def __init__(self, api, fields):
        self.api = api
        dict.__init__(fields)

    def commit(self):
        # XXX
        pass

    def delete(self):
        # XXX
        pass

class Slices(Table):
    """
    Representation of row(s) from the slices table in the
    database.
    """

    def __init__(self, api, slice_id_list = None):
        # XXX
        pass
