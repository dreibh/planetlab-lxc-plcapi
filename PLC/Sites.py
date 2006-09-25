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
import PLC.Persons

class Site(Row):
    """
    Representation of a row in the sites table. To use, optionally
    instantiate with a dict of values. Update as you would a
    dict. Commit to the database with sync().
    """

    fields = {
        'site_id': Parameter(int, "Site identifier"),
        'name': Parameter(str, "Full site name", max = 254),
        'abbreviated_name': Parameter(str, "Abbreviated site name", max = 50),
        'login_base': Parameter(str, "Site slice prefix", max = 20),
        'is_public': Parameter(bool, "Publicly viewable site"),
        'latitude': Parameter(float, "Decimal latitude of the site", min = -90.0, max = 90.0),
        'longitude': Parameter(float, "Decimal longitude of the site", min = -180.0, max = 180.0),
        'url': Parameter(str, "URL of a page that describes the site", max = 254),
        'date_created': Parameter(str, "Date and time when site entry was created"),        
        'last_updated': Parameter(str, "Date and time when site entry was last updated"),        
        'deleted': Parameter(bool, "Has been deleted"),
        'max_slices': Parameter(int, "Maximum number of slices that the site is able to create"),
        'person_ids': Parameter([int], "List of account identifiers"),
        # 'slice_ids': Parameter([int], "List of slice identifiers"),
        # 'pcu_ids': Parameter([int], "List of PCU identifiers"),
        'node_ids': Parameter([int], "List of site node identifiers"),
        }

    def __init__(self, api, fields):
        Row.__init__(self, fields)
        self.api = api

    def validate_login_base(self, login_base):
        if not set(login_base).issubset(string.ascii_letters):
            raise PLCInvalidArgument, "Login base must consist only of ASCII letters"

        login_base = login_base.lower()
        conflicts = Sites(self.api, [login_base])
        for site_id, site in conflicts.iteritems():
            if not site['deleted'] and ('site_id' not in self or self['site_id'] != site_id):
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
        self.api.db.do("INSERT INTO person_site (person_id, site_id)" \
                       " VALUES(%(person_id)d, %(site_id)d)",
                       locals())

        if commit:
            self.api.db.commit()

        if 'person_ids' in self and person_id not in self['person_ids']:
            self['person_ids'].append(person_id)

        if 'site_ids' in person and site_id not in person['site_ids']:
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
        self.api.db.do("DELETE FROM person_site" \
                       " WHERE person_id = %(person_id)d" \
                       " AND site_id = %(site_id)d",
                       locals())

        if commit:
            self.api.db.commit()

        if 'person_ids' in self and person_id in self['person_ids']:
            self['person_ids'].remove(person_id)

        if 'site_ids' in person and site_id in person['site_ids']:
            person['site_ids'].remove(site_id)

    def sync(self, commit = True):
        """
        Flush changes back to the database.
        """

        self.validate()

        try:
            if not self['name'] or \
               not self['abbreviated_name'] or \
               not self['login_base']:
                raise KeyError
        except KeyError:
            raise PLCInvalidArgument, "name, abbreviated_name, and login_base must all be specified"

        # Fetch a new site_id if necessary
        if 'site_id' not in self:
            rows = self.api.db.selectall("SELECT NEXTVAL('sites_site_id_seq') AS site_id")
            if not rows:
                raise PLCDBError, "Unable to fetch new site_id"
            self['site_id'] = rows[0]['site_id']
            insert = True
        else:
            insert = False

        # Filter out fields that cannot be set or updated directly
        sites_fields = self.api.db.fields('sites')
        fields = dict(filter(lambda (key, value): key in sites_fields,
                             self.items()))

        # Parameterize for safety
        keys = fields.keys()
        values = [self.api.db.param(key, value) for (key, value) in fields.items()]

        if insert:
            # Insert new row in sites table
            sql = "INSERT INTO sites (%s) VALUES (%s)" % \
                  (", ".join(keys), ", ".join(values))
        else:
            # Update existing row in sites table
            columns = ["%s = %s" % (key, value) for (key, value) in zip(keys, values)]
            sql = "UPDATE sites SET " + \
                  ", ".join(columns) + \
                  " WHERE site_id = %(site_id)d"

        self.api.db.do(sql, fields)

        if commit:
            self.api.db.commit()

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
                if person_site_id != self['site_id'] and \
                   not person_site['deleted']:
                    delete = False
                    break

            if delete:
                person.delete(commit = False)

        # Delete all site slices
        # slices = Slices(self.api, self['slice_ids'])
        # for slice in slices.values():
        #    slice.delete(commit = False)

        # Delete all site PCUs
        # pcus = PCUs(self.api, self['pcu_ids'])
        # for pcu in pcus.values():
        #    pcu.delete(commit = False)

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
    database. Specify extra_fields to be able to view and modify extra
    fields.
    """

    def __init__(self, api, site_id_or_login_base_list = None, fields = Site.fields):
        self.api = api

        sql = "SELECT %s FROM view_sites WHERE deleted IS False" % \
              ", ".join(fields)

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
            for aggregate in ['person_ids', 'slice_ids',
                              'defaultattribute_ids', 'pcu_ids', 'node_ids']:
                if not site.has_key(aggregate) or site[aggregate] is None:
                    site[aggregate] = []
                else:
                    site[aggregate] = map(int, site[aggregate].split(','))
