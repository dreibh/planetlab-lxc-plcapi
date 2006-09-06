from types import StringTypes

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Debug import profile
from PLC.Table import Row, Table

class Address(Row):
    """
    Representation of a row in the addresses table. To use, instantiate
    with a dict of values.
    """

    fields = {
        'address_id': Parameter(int, "Address type"),
        'address_type_id': Parameter(int, "Address type identifier"),
        'address_type': Parameter(str, "Address type name"),
        'line1': Parameter(str, "Address line 1"),
        'line2': Parameter(str, "Address line 2"),
        'line3': Parameter(str, "Address line 3"),
        'city': Parameter(str, "City"),
        'state': Parameter(str, "State or province"),
        'postalcode': Parameter(str, "Postal code"),
        'country': Parameter(str, "Country"),
        }

    def __init__(self, api, fields):
        self.api = api
        dict.__init__(fields)

    def flush(self, commit = True):
        # XXX
        pass

    def delete(self, commit = True):
        # XXX
        pass

class Addresses(Table):
    """
    Representation of row(s) from the addresses table in the
    database.
    """

    def __init__(self, api, address_id_list = None):
        # XXX
        pass
