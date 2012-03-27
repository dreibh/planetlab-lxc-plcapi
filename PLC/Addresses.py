from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Table import Row, Table
from PLC.Filter import Filter
from PLC.AddressTypes import AddressType, AddressTypes

class Address(Row):
    """
    Representation of a row in the addresses table. To use, instantiate
    with a dict of values.
    """

    table_name = 'addresses'
    primary_key = 'address_id'
    join_tables = ['address_address_type', 'site_address']
    fields = {
        'address_id': Parameter(int, "Address identifier"),
        'line1': Parameter(str, "Address line 1", max = 254),
        'line2': Parameter(str, "Address line 2", max = 254, nullok = True),
        'line3': Parameter(str, "Address line 3", max = 254, nullok = True),
        'city': Parameter(str, "City", max = 254),
        'state': Parameter(str, "State or province", max = 254),
        'postalcode': Parameter(str, "Postal code", max = 64),
        'country': Parameter(str, "Country", max = 128),
        'address_type_ids': Parameter([int], "Address type identifiers"),
        'address_types': Parameter([str], "Address types"),
        }

    def add_address_type(self, address_type, commit = True):
        """
        Add address type to existing address.
        """

        assert 'address_id' in self
        assert isinstance(address_type, AddressType)
        assert 'address_type_id' in address_type

        address_id = self['address_id']
        address_type_id = address_type['address_type_id']

        if address_type_id not in self['address_type_ids']:
            assert address_type['name'] not in self['address_types']

            self.api.db.do("INSERT INTO address_address_type (address_id, address_type_id)" \
                           " VALUES(%(address_id)d, %(address_type_id)d)",
                           locals())

            if commit:
                self.api.db.commit()

            self['address_type_ids'].append(address_type_id)
            self['address_types'].append(address_type['name'])

    def remove_address_type(self, address_type, commit = True):
        """
        Add address type to existing address.
        """

        assert 'address_id' in self
        assert isinstance(address_type, AddressType)
        assert 'address_type_id' in address_type

        address_id = self['address_id']
        address_type_id = address_type['address_type_id']

        if address_type_id in self['address_type_ids']:
            assert address_type['name'] in self['address_types']

            self.api.db.do("DELETE FROM address_address_type" \
                           " WHERE address_id = %(address_id)d" \
                           " AND address_type_id = %(address_type_id)d",
                           locals())

            if commit:
                self.api.db.commit()

            self['address_type_ids'].remove(address_type_id)
            self['address_types'].remove(address_type['name'])

class Addresses(Table):
    """
    Representation of row(s) from the addresses table in the
    database.
    """

    def __init__(self, api, address_filter = None, columns = None):
        Table.__init__(self, api, Address, columns)

        sql = "SELECT %s FROM view_addresses WHERE True" % \
              ", ".join(self.columns)

        if address_filter is not None:
            if isinstance(address_filter, (list, tuple, set, int, long)):
                address_filter = Filter(Address.fields, {'address_id': address_filter})
            elif isinstance(address_filter, dict):
                address_filter = Filter(Address.fields, address_filter)
            sql += " AND (%s) %s" % address_filter.sql(api)

        self.selectall(sql)
