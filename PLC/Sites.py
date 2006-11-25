from types import StringTypes
import string

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Debug import profile
from PLC.Table import Row, Table
from PLC.Slices import Slice, Slices
from PLC.PCUs import PCU, PCUs
from PLC.Nodes import Node, Nodes
from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.Addresses import Address, Addresses
import PLC.Persons

class Site(Row):
    """
    Representation of a row in the sites table. To use, optionally
    instantiate with a dict of values. Update as you would a
    dict. Commit to the database with sync().
    """

    table_name = 'sites'
    primary_key = 'site_id'
    fields = {
        'site_id': Parameter(int, "Site identifier"),
        'name': Parameter(str, "Full site name", max = 254),
        'abbreviated_name': Parameter(str, "Abbreviated site name", max = 50),
        'login_base': Parameter(str, "Site slice prefix", max = 20),
        'is_public': Parameter(bool, "Publicly viewable site"),
        'latitude': Parameter(float, "Decimal latitude of the site", min = -90.0, max = 90.0, nullok = True),
        'longitude': Parameter(float, "Decimal longitude of the site", min = -180.0, max = 180.0, nullok = True),
        'url': Parameter(str, "URL of a page that describes the site", max = 254, nullok = True),
        'date_created': Parameter(int, "Date and time when site entry was created, in seconds since UNIX epoch", ro = True),
        'last_updated': Parameter(int, "Date and time when site entry was last updated, in seconds since UNIX epoch", ro = True),
        'max_slices': Parameter(int, "Maximum number of slices that the site is able to create"),
        'max_slivers': Parameter(int, "Maximum number of slivers that the site is able to create"),
        'person_ids': Parameter([int], "List of account identifiers"),
        'slice_ids': Parameter([int], "List of slice identifiers"),
        'address_ids': Parameter([int], "List of address identifiers"),
        'pcu_ids': Parameter([int], "List of PCU identifiers"),
        'node_ids': Parameter([int], "List of site node identifiers"),
        'peer_id': Parameter(int, "Peer at which this slice was created", nullok = True),
        }

    # for Cache
    class_key = 'login_base'
    foreign_fields = ['abbreviated_name', 'name', 'is_public', 'latitude', 'longitude',
		      'url', 'date_created', 'last_updated', 'max_slices', 'max_slivers',
		      ]
    foreign_xrefs = {
#'person_ids',
#'slice_ids',
#'node_ids',
#'address_ids',
#'pcu_ids',
}

    def validate_name(self, name):
        if not len(name):
            raise PLCInvalidArgument, "Name must be specified"

        return name

    validate_abbreviated_name = validate_name

    def validate_login_base(self, login_base):
        if not len(login_base):
            raise PLCInvalidArgument, "Login base must be specified"

        if not set(login_base).issubset(string.ascii_letters.lower()):
            raise PLCInvalidArgument, "Login base must consist only of lowercase ASCII letters"

        conflicts = Sites(self.api, [login_base])
        for site in conflicts:
            if 'site_id' not in self or self['site_id'] != site['site_id']:
                raise PLCInvalidArgument, "login_base already in use"

        return login_base

    def validate_latitude(self, latitude):
        if not self.has_key('longitude') or \
           self['longitude'] is None:
            raise PLCInvalidArgument, "Longitude must also be specified"

        return latitude

    def validate_longitude(self, longitude):
        if not self.has_key('latitude') or \
           self['latitude'] is None:
            raise PLCInvalidArgument, "Latitude must also be specified"

        return longitude

    def add_person(self, person, commit = True):
        """
        Add person to existing site.
        """

        assert 'site_id' in self
        assert isinstance(person, PLC.Persons.Person)
        assert 'person_id' in person

        site_id = self['site_id']
        person_id = person['person_id']

        if person_id not in self['person_ids']:
            assert site_id not in person['site_ids']

            self.api.db.do("INSERT INTO person_site (person_id, site_id)" \
                           " VALUES(%(person_id)d, %(site_id)d)",
                           locals())

            if commit:
                self.api.db.commit()

            self['person_ids'].append(person_id)
            person['site_ids'].append(site_id)

    def remove_person(self, person, commit = True):
        """
        Remove person from existing site.
        """

        assert 'site_id' in self
        assert isinstance(person, PLC.Persons.Person)
        assert 'person_id' in person

        site_id = self['site_id']
        person_id = person['person_id']

        if person_id in self['person_ids']:
            assert site_id in person['site_ids']

            self.api.db.do("DELETE FROM person_site" \
                           " WHERE person_id = %(person_id)d" \
                           " AND site_id = %(site_id)d",
                           locals())

            if commit:
                self.api.db.commit()

            self['person_ids'].remove(person_id)
            person['site_ids'].remove(site_id)

    def add_address(self, address, commit = True):
        """
        Add address to existing site.
        """

        assert 'site_id' in self
        assert isinstance(address, Address)
        assert 'address_id' in address

        site_id = self['site_id']
        address_id = address['address_id']

        if address_id not in self['address_ids']:
            self.api.db.do("INSERT INTO site_address (address_id, site_id)" \
                           " VALUES(%(address_id)d, %(site_id)d)",
                           locals())

            if commit:
                self.api.db.commit()

            self['address_ids'].append(address_id)

    def remove_address(self, address, commit = True):
        """
        Remove address from existing site.
        """

        assert 'site_id' in self
        assert isinstance(address, Address)
        assert 'address_id' in address

        site_id = self['site_id']
        address_id = address['address_id']

        if address_id in self['address_ids']:
            self.api.db.do("DELETE FROM site_address" \
                           " WHERE address_id = %(address_id)d" \
                           " AND site_id = %(site_id)d",
                           locals())

            if commit:
                self.api.db.commit()

            self['address_ids'].remove(address_id)

    def delete(self, commit = True):
        """
        Delete existing site.
        """

        assert 'site_id' in self

        # Delete accounts of all people at the site who are not
        # members of at least one other non-deleted site.
        persons = PLC.Persons.Persons(self.api, self['person_ids'])
        for person in persons:
            delete = True

            person_sites = Sites(self.api, person['site_ids'])
            for person_site in person_sites:
                if person_site['site_id'] != self['site_id']:
                    delete = False
                    break

            if delete:
                person.delete(commit = False)

        # Delete all site addresses
        addresses = Addresses(self.api, self['address_ids'])
        for address in addresses:
            address.delete(commit = False)

        # Delete all site slices
        slices = Slices(self.api, self['slice_ids'])
        for slice in slices:
            slice.delete(commit = False)

        # Delete all site PCUs
        pcus = PCUs(self.api, self['pcu_ids'])
        for pcu in pcus:
            pcu.delete(commit = False)

        # Delete all site nodes
        nodes = Nodes(self.api, self['node_ids'])
        for node in nodes:
            node.delete(commit = False)

        # Clean up miscellaneous join tables
        for table in ['person_site']:
            self.api.db.do("DELETE FROM %s" \
                           " WHERE site_id = %d" % \
                           (table, self['site_id']), self)

        # Mark as deleted
        self['deleted'] = True
        self.sync(commit)

class Sites(Table):
    """
    Representation of row(s) from the sites table in the
    database.
    """

    def __init__(self, api, site_filter = None, columns = None):
        Table.__init__(self, api, Site, columns)

        sql = "SELECT %s FROM view_sites WHERE deleted IS False" % \
              ", ".join(self.columns)

        if site_filter is not None:
            if isinstance(site_filter, (list, tuple, set)):
                # Separate the list into integers and strings
                ints = filter(lambda x: isinstance(x, (int, long)), site_filter)
                strs = filter(lambda x: isinstance(x, StringTypes), site_filter)
                site_filter = Filter(Site.fields, {'site_id': ints, 'login_base': strs})
                sql += " AND (%s)" % site_filter.sql(api, "OR")
            elif isinstance(site_filter, dict):
                site_filter = Filter(Site.fields, site_filter)
                sql += " AND (%s)" % site_filter.sql(api, "AND")

        self.selectall(sql)
