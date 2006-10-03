from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Table import Row, Table

class Address(Row):
    """
    Representation of a row in the addresses table. To use, instantiate
    with a dict of values.
    """

    table_name = 'addresses'
    primary_key = 'address_id'
    fields = {
        'address_id': Parameter(int, "Address identifier"),
        'line1': Parameter(str, "Address line 1"),
        'line2': Parameter(str, "Address line 2"),
        'line3': Parameter(str, "Address line 3"),
        'city': Parameter(str, "City"),
        'state': Parameter(str, "State or province"),
        'postalcode': Parameter(str, "Postal code"),
        'country': Parameter(str, "Country"),
        'address_type': Parameter(str, "Address type"),
        }

    def __init__(self, api, fields = {}):
        self.api = api
        Row.__init__(self, fields)

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
