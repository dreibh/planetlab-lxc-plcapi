from types import StringTypes

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Debug import profile
from PLC.Table import Row, Table

class Key(Row):
    """
    Representation of a row in the keys table. To use, instantiate
    with a dict of values.
    """

    fields = {
        'key_id': Parameter(int, "Key type"),
        'key_type': Parameter(str, "Key type"),
        'key': Parameter(str, "Key value"),
        'last_updated': Parameter(str, "Date and time of last update"),
        'is_blacklisted': Parameter(str, "Key has been blacklisted and is forever unusable"),
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

class Keys(Table):
    """
    Representation of row(s) from the keys table in the
    database.
    """

    def __init__(self, api, key_id_list = None):
        # XXX
        pass
