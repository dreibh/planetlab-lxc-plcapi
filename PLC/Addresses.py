from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Table import Row, Table
from PLC.AddressTypes import AddressType, AddressTypes

class Address(Row):
    """
    Representation of a row in the addresses table. To use, instantiate
    with a dict of values.
    """

    table_name = 'addresses'
    primary_key = 'address_id'
    fields = {
        'address_id': Parameter(int, "Address identifier"),
        'line1': Parameter(str, "Address line 1", max = 254, optional = False),
        'line2': Parameter(str, "Address line 2", max = 254),
        'line3': Parameter(str, "Address line 3", max = 254),
        'city': Parameter(str, "City", max = 254, optional = False),
        'state': Parameter(str, "State or province", max = 254, optional = False),
        'postalcode': Parameter(str, "Postal code", max = 64, optional = False),
        'country': Parameter(str, "Country", max = 128, optional = False),
        'site_id': Parameter(str, "Site identifier"),
        'address_type_ids': Parameter([int], "Address type identifiers", ro = True),
        'address_types': Parameter([str], "Address types", ro = True),
        }

    def __init__(self, api, fields = {}):
        Row.__init__(self, fields)
        self.api = api

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

    def delete(self, commit = True):
        """
        Delete existing address from the database.
        """

        assert 'address_id' in self

        # Clean up miscellaneous join tables
        for table in ['address_address_type', 'addresses']:
            self.api.db.do("DELETE FROM %s" \
                           " WHERE address_id = %d" % \
                           (table, self['address_id']), self)

        if commit:
            self.api.db.commit()

class Addresses(Table):
    """
    Representation of row(s) from the addresses table in the
    database.
    """

    def __init__(self, api, address_id_list = None):
	self.api = api

        sql = "SELECT %s FROM view_addresses" % \
              ", ".join(Address.fields)

        if address_id_list:
            sql += " WHERE address_id IN (%s)" % ", ".join(map(str, address_id_list))

        rows = self.api.db.selectall(sql)

        for row in rows:
            self[row['address_id']] = address = Address(api, row)
            for aggregate in 'address_type_ids', 'address_types':
                if not address.has_key(aggregate) or address[aggregate] is None:
                    address[aggregate] = []
                else:
                    elements = address[aggregate].split(',')
                    try:
                        address[aggregate] = map(int, elements)
                    except ValueError:
                        address[aggregate] = elements
