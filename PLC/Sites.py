from types import StringTypes
import string

from PLC.Faults import *
from PLC.Parameter import Parameter
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
        'latitude': Parameter(float, "Decimal latitude of the site", min = -90.0, max = 90.0),
        'longitude': Parameter(float, "Decimal longitude of the site", min = -180.0, max = 180.0),
        'url': Parameter(str, "URL of a page that describes the site", max = 254),
        'date_created': Parameter(int, "Date and time when site entry was created, in seconds since UNIX epoch", ro = True),
        'last_updated': Parameter(int, "Date and time when site entry was last updated, in seconds since UNIX epoch", ro = True),
        'max_slices': Parameter(int, "Maximum number of slices that the site is able to create"),
        'max_slivers': Parameter(int, "Maximum number of slivers that the site is able to create"),
        'person_ids': Parameter([int], "List of account identifiers", ro = True),
        'slice_ids': Parameter([int], "List of slice identifiers", ro = True),
        'address_ids': Parameter([int], "List of address identifiers", ro = True),
        'pcu_ids': Parameter([int], "List of PCU identifiers", ro = True),
        'node_ids': Parameter([int], "List of site node identifiers", ro = True),
        }

    def __init__(self, api, fields = {}):
        Row.__init__(self, fields)
        self.api = api

    def validate_name(self, name):
        name = name.strip()
        if not name:
            raise PLCInvalidArgument, "Name must be specified"

        return name

    validate_abbreviated_name = validate_name

    def validate_login_base(self, login_base):
        login_base = login_base.strip().lower()

        if not login_base:
            raise PLCInvalidArgument, "Login base must be specified"

        if not set(login_base).issubset(string.ascii_letters):
            raise PLCInvalidArgument, "Login base must consist only of ASCII letters"

        conflicts = Sites(self.api, [login_base])
        for site_id, site in conflicts.iteritems():
            if 'site_id' not in self or self['site_id'] != site_id:
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

    def delete(self, commit = True):
        """
        Delete existing site.
        """

        assert 'site_id' in self

        # Delete accounts of all people at the site who are not
        # members of at least one other non-deleted site.
        persons = PLC.Persons.Persons(self.api, self['person_ids'])
        for person_id, person in persons.iteritems():
            delete = True

            person_sites = Sites(self.api, person['site_ids'])
            for person_site_id, person_site in person_sites.iteritems():
                if person_site_id != self['site_id']:
                    delete = False
                    break

            if delete:
                person.delete(commit = False)

        # Delete all site addresses
        addresses = Addresses(self.api, self['address_ids'])
        for address in addresses.values():
           address.delete(commit = False)

        # Delete all site slices
        slices = Slices(self.api, self['slice_ids'])
        for slice in slices.values():
           slice.delete(commit = False)

        # Delete all site PCUs
        pcus = PCUs(self.api, self['pcu_ids'])
        for pcu in pcus.values():
           pcu.delete(commit = False)

        # Delete all site nodes
        nodes = Nodes(self.api, self['node_ids'])
        for node in nodes.values():
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
    database. Specify fields to limit columns to just the specified
    fields.
    """

    def __init__(self, api, site_id_or_login_base_list = None):
        self.api = api

        sql = "SELECT %s FROM view_sites WHERE deleted IS False" % \
              ", ".join(Site.fields)

        if site_id_or_login_base_list:
            # Separate the list into integers and strings
            site_ids = filter(lambda site_id: isinstance(site_id, (int, long)),
                              site_id_or_login_base_list)
            login_bases = filter(lambda login_base: isinstance(login_base, StringTypes),
                                 site_id_or_login_base_list)
            sql += " AND (False"
            if site_ids:
                sql += " OR site_id IN (%s)" % ", ".join(map(str, site_ids))
            if login_bases:
                sql += " OR login_base IN (%s)" % ", ".join(api.db.quote(login_bases))
            sql += ")"

        rows = self.api.db.selectall(sql)

        for row in rows:
            self[row['site_id']] = site = Site(api, row)
            for aggregate in ['person_ids', 'slice_ids', 'address_ids',
                              'pcu_ids', 'node_ids']:
                if not site.has_key(aggregate) or site[aggregate] is None:
                    site[aggregate] = []
                else:
                    site[aggregate] = map(int, site[aggregate].split(','))
