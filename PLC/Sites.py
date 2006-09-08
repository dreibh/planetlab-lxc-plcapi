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
    dict. Commit to the database with flush().
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
        'nodegroup_id': Parameter(int, "Identifier of the nodegroup containing the site's nodes"),
        'organization_id': Parameter(int, "Organizational identifier if the site is part of a larger organization"),
        'ext_consortium_id': Parameter(int, "Consortium identifier if the site is part of an external consortium"),
        'date_created': Parameter(str, "Date and time when node entry was created"),        
        'deleted': Parameter(bool, "Has been deleted"),
        }

    # These fields are derived from join tables and are not actually
    # in the sites table.
    join_fields = {
        'max_slices': Parameter(int, "Maximum number of slices that the site is able to create"),
        'site_share': Parameter(float, "Relative resource share for this site's slices"),
        }        

    # These fields are derived from join tables and are not returned
    # by default unless specified.
    extra_fields = {
        'person_ids': Parameter([int], "List of account identifiers"),
        'slice_ids': Parameter([int], "List of slice identifiers"),
        'defaultattribute_ids': Parameter([int], "List of default slice attribute identifiers"),
        'pcu_ids': Parameter([int], "List of PCU identifiers"),
        'node_ids': Parameter([int], "List of site node identifiers"),
        }

    default_fields = dict(fields.items() + join_fields.items())
    all_fields = dict(default_fields.items() + extra_fields.items())

    # Number of slices assigned to each site at the time that the site is created
    default_max_slices = 0

    # XXX Useless, unclear what this value means
    default_site_share = 1.0

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

    def validate_nodegroup_id(self, nodegroup_id):
        nodegroups = NodeGroups(self.api)
        if nodegroup_id not in nodegroups:
            raise PLCInvalidArgument, "No such nodegroup"

        return nodegroup_id

    def validate_organization_id(self, organization_id):
        organizations = Organizations(self.api)
        if role_id not in organizations:
            raise PLCInvalidArgument, "No such organization"

        return organization_id

    def validate_ext_consortium_id(self, organization_id):
        consortiums = Consortiums(self.api)
        if consortium_id not in consortiums:
            raise PLCInvalidArgument, "No such consortium"

        return nodegroup_id

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

    def flush(self, commit = True):
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

        # Create site node group if necessary
        if 'nodegroup_id' not in self:
            rows = self.api.db.selectall("SELECT NEXTVAL('nodegroups_nodegroup_id_seq') as nodegroup_id")
            if not rows:
                raise PLCDBError, "Unable to fetch new nodegroup_id"
            self['nodegroup_id'] = rows[0]['nodegroup_id']

            nodegroup_id = self['nodegroup_id']
            # XXX Needs a unique name because we cannot delete site node groups yet
            name = self['login_base'] + str(self['site_id'])
            description = "Nodes at " + self['login_base']
            is_custom = False
            self.api.db.do("INSERT INTO nodegroups (nodegroup_id, name, description, is_custom)" \
                           " VALUES (%(nodegroup_id)d, %(name)s, %(description)s, %(is_custom)s)",
                           locals())

        # Filter out fields that cannot be set or updated directly
        fields = dict(filter(lambda (key, value): key in self.fields,
                             self.items()))

        # Parameterize for safety
        keys = fields.keys()
        values = [self.api.db.param(key, value) for (key, value) in fields.items()]

        if insert:
            # Insert new row in sites table
            self.api.db.do("INSERT INTO sites (%s) VALUES (%s)" % \
                           (", ".join(keys), ", ".join(values)),
                           fields)

            # Setup default slice site info
            # XXX Will go away soon
            self['max_slices'] = self.default_max_slices
            self['site_share'] = self.default_site_share
            self.api.db.do("INSERT INTO dslice03_siteinfo (site_id, max_slices, site_share)" \
                           " VALUES (%(site_id)d, %(max_slices)d, %(site_share)f)",
                           self)
        else:
            # Update default slice site info
            # XXX Will go away soon
            if 'max_slices' in self and 'site_share' in self:
                self.api.db.do("UPDATE dslice03_siteinfo SET " \
                               " max_slices = %(max_slices)d, site_share = %(site_share)f" \
                               " WHERE site_id = %(site_id)d",
                               self)

            # Update existing row in sites table
            columns = ["%s = %s" % (key, value) for (key, value) in zip(keys, values)]
            self.api.db.do("UPDATE sites SET " + \
                           ", ".join(columns) + \
                           " WHERE site_id = %(site_id)d",
                           fields)

        if commit:
            self.api.db.commit()

    def delete(self, commit = True):
        """
        Delete existing site.
        """

        assert 'site_id' in self

        # Make sure extra fields are present
        sites = Sites(self.api, [self['site_id']],
                      ['person_ids', 'slice_ids', 'pcu_ids', 'node_ids'])
        assert sites
        self.update(sites.values()[0])

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
        for table in ['site_authorized_subnets',
                      'dslice03_defaultattribute',
                      'dslice03_siteinfo']:
            self.api.db.do("DELETE FROM %s" \
                           " WHERE site_id = %d" % \
                           (table, self['site_id']))

        # XXX Cannot delete site node groups yet

        # Mark as deleted
        self['deleted'] = True
        self.flush(commit)

class Sites(Table):
    """
    Representation of row(s) from the sites table in the
    database. Specify extra_fields to be able to view and modify extra
    fields.
    """

    def __init__(self, api, site_id_or_login_base_list = None, extra_fields = []):
        self.api = api

        sql = "SELECT sites.*" \
              ", dslice03_siteinfo.max_slices"

        # N.B.: Joined IDs may be marked as deleted in their primary tables
        join_tables = {
            # extra_field: (extra_table, extra_column, join_using)
            'person_ids': ('person_site', 'person_id', 'site_id'),
            'slice_ids': ('dslice03_slices', 'slice_id', 'site_id'),
            'defaultattribute_ids': ('dslice03_defaultattribute', 'defaultattribute_id', 'site_id'),
            'pcu_ids': ('pcu', 'pcu_id', 'site_id'),
            'node_ids': ('nodegroup_nodes', 'node_id', 'nodegroup_id'),
            }

        extra_fields = filter(join_tables.has_key, extra_fields)
        extra_tables = ["%s USING (%s)" % \
                        (join_tables[field][0], join_tables[field][2]) \
                        for field in extra_fields]
        extra_columns = ["%s.%s" % \
                         (join_tables[field][0], join_tables[field][1]) \
                         for field in extra_fields]

        if extra_columns:
            sql += ", " + ", ".join(extra_columns)

        sql += " FROM sites" \
               " LEFT JOIN dslice03_siteinfo USING (site_id)"

        if extra_tables:
            sql += " LEFT JOIN " + " LEFT JOIN ".join(extra_tables)

        sql += " WHERE sites.deleted IS False"

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
            if self.has_key(row['site_id']):
                site = self[row['site_id']]
                site.update(row)
            else:
                self[row['site_id']] = Site(api, row)
