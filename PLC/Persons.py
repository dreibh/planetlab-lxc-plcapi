#
# Functions for interacting with the persons table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: Persons.py,v 1.1 2006/09/06 15:36:07 mlhuang Exp $
#

from types import StringTypes
from datetime import datetime
import md5
import time
from random import Random
import re

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Debug import profile
from PLC.Table import Row, Table
from PLC.Roles import Roles
from PLC.Addresses import Address, Addresses
from PLC.Keys import Key, Keys
from PLC import md5crypt
import PLC.Sites

class Person(Row):
    """
    Representation of a row in the persons table. To use, optionally
    instantiate with a dict of values. Update as you would a
    dict. Commit to the database with flush().
    """

    fields = {
        'person_id': Parameter(int, "Account identifier"),
        'first_name': Parameter(str, "Given name"),
        'last_name': Parameter(str, "Surname"),
        'title': Parameter(str, "Title"),
        'email': Parameter(str, "Primary e-mail address"),
        'phone': Parameter(str, "Telephone number"),
        'url': Parameter(str, "Home page"),
        'bio': Parameter(str, "Biography"),
        'accepted_aup': Parameter(bool, "Has accepted the AUP"),
        'enabled': Parameter(bool, "Has been enabled"),
        'deleted': Parameter(bool, "Has been deleted"),
        'password': Parameter(str, "Account password in crypt() form"),
        'last_updated': Parameter(str, "Date and time of last update"),
        'date_created': Parameter(str, "Date and time when account was created"),
        }

    # These fields are derived from join tables and are not actually
    # in the persons table.
    join_fields = {
        'role_ids': Parameter([int], "List of role identifiers"),
        'roles': Parameter([str], "List of roles"),
        'site_ids': Parameter([int], "List of site identifiers"),
        }
    
    # These fields are derived from join tables and are not returned
    # by default unless specified.
    extra_fields = {
        'address_ids': Parameter([int], "List of address identifiers"),
        'key_ids': Parameter([int], "List of key identifiers"),
        'slice_ids': Parameter([int], "List of slice identifiers"),
        }

    default_fields = dict(fields.items() + join_fields.items())
    all_fields = dict(default_fields.items() + extra_fields.items())

    def __init__(self, api, fields):
        Row.__init__(self, fields)
        self.api = api

    def validate_email(self, email):
        """
        Validate email address. Stolen from Mailman.
        """

        invalid_email = PLCInvalidArgument("Invalid e-mail address")
        email_badchars = r'[][()<>|;^,\200-\377]'

        # Pretty minimal, cheesy check.  We could do better...
        if not email or email.count(' ') > 0:
            raise invalid_email
        if re.search(email_badchars, email) or email[0] == '-':
            raise invalid_email

        email = email.lower()
        at_sign = email.find('@')
        if at_sign < 1:
            raise invalid_email
        user = email[:at_sign]
        rest = email[at_sign+1:]
        domain = rest.split('.')

        # This means local, unqualified addresses, are no allowed
        if not domain:
            raise invalid_email
        if len(domain) < 2:
            raise invalid_email

        conflicts = Persons(self.api, [email])
        for person_id, person in conflicts.iteritems():
            if not person['deleted'] and ('person_id' not in self or self['person_id'] != person_id):
                raise PLCInvalidArgument, "E-mail address already in use"

        return email

    def validate_password(self, password):
        """
        Encrypt password if necessary before committing to the
        database.
        """

        if len(password) > len(md5crypt.MAGIC) and \
           password[0:len(md5crypt.MAGIC)] == md5crypt.MAGIC:
            return password
        else:
            # Generate a somewhat unique 2 character salt string
            salt = str(time.time()) + str(Random().random())
            salt = md5.md5(salt).hexdigest()[:8] 
            return md5crypt.md5crypt(password, salt)

    def validate_role_ids(self, role_ids):
        """
        Ensure that the specified role_ids are all valid.
        """

        roles = Roles(self.api)
        for role_id in role_ids:
            if role_id not in roles:
                raise PLCInvalidArgument, "No such role"

        return role_ids

    def validate_site_ids(self, site_ids):
        """
        Ensure that the specified site_ids are all valid.
        """

        sites = PLC.Sites.Sites(self.api, site_ids)
        for site_id in site_ids:
            if site_id not in sites:
                raise PLCInvalidArgument, "No such site"

        return site_ids

    def can_update(self, person):
        """
        Returns true if we can update the specified person. We can
        update a person if:

        1. We are the person.
        2. We are an admin.
        3. We are a PI and the person is a user or tech or at
           one of our sites.
        """

        assert isinstance(person, Person)

        if self['person_id'] == person['person_id']:
            return True

        if 'admin' in self['roles']:
            return True

        if 'pi' in self['roles']:
            if set(self['site_ids']).intersection(person['site_ids']):
                # Can update people with higher role IDs
                return min(self['role_ids']) < min(person['role_ids'])

        return False

    def can_view(self, person):
        """
        Returns true if we can view the specified person. We can
        view a person if:

        1. We are the person.
        2. We are an admin.
        3. We are a PI and the person is at one of our sites.
        """

        assert isinstance(person, Person)

        if self.can_update(person):
            return True

        if 'pi' in self['roles']:
            if set(self['site_ids']).intersection(person['site_ids']):
                # Can view people with equal or higher role IDs
                return min(self['role_ids']) <= min(person['role_ids'])

        return False

    def add_role(self, role_id, commit = True):
        """
        Add role to existing account.
        """

        assert 'person_id' in self

        person_id = self['person_id']
        self.api.db.do("INSERT INTO person_roles (person_id, role_id)" \
                       " VALUES(%(person_id)d, %(role_id)d)",
                       locals())

        if commit:
            self.api.db.commit()

        assert 'role_ids' in self
        if role_id not in self['role_ids']:
            self['role_ids'].append(role_id)

    def remove_role(self, role_id, commit = True):
        """
        Remove role from existing account.
        """

        assert 'person_id' in self

        person_id = self['person_id']
        self.api.db.do("DELETE FROM person_roles" \
                       " WHERE person_id = %(person_id)d" \
                       " AND role_id = %(role_id)d",
                       locals())

        if commit:
            self.api.db.commit()

        assert 'role_ids' in self
        if role_id in self['role_ids']:
            self['role_ids'].remove(role_id)

    def set_primary_site(self, site, commit = True):
        """
        Set the primary site for an existing account.
        """

        assert 'person_id' in self
        assert isinstance(site, PLC.Sites.Site)
        assert 'site_id' in site

        person_id = self['person_id']
        site_id = site['site_id']
        self.api.db.do("UPDATE person_site SET is_primary = False" \
                       " WHERE person_id = %(person_id)d",
                       locals())
        self.api.db.do("UPDATE person_site SET is_primary = True" \
                       " WHERE person_id = %(person_id)d" \
                       " AND site_id = %(site_id)d",
                       locals())

        if commit:
            self.api.db.commit()

        assert 'site_ids' in self
        assert site_id in self['site_ids']

        # Make sure that the primary site is first in the list
        self['site_ids'].remove(site_id)
        self['site_ids'].insert(0, site_id)

    def flush(self, commit = True):
        """
        Commit changes back to the database.
        """

        self.validate()

        # Fetch a new person_id if necessary
        if 'person_id' not in self:
            rows = self.api.db.selectall("SELECT NEXTVAL('persons_person_id_seq') AS person_id")
            if not rows:
                raise PLCDBError, "Unable to fetch new person_id"
            self['person_id'] = rows[0]['person_id']
            insert = True
        else:
            insert = False

        # Filter out fields that cannot be set or updated directly
        fields = dict(filter(lambda (key, value): key in self.fields,
                             self.items()))

        # Parameterize for safety
        keys = fields.keys()
        values = [self.api.db.param(key, value) for (key, value) in fields.items()]

        if insert:
            # Insert new row in persons table
            sql = "INSERT INTO persons (%s) VALUES (%s)" % \
                  (", ".join(keys), ", ".join(values))
        else:
            # Update existing row in persons table
            columns = ["%s = %s" % (key, value) for (key, value) in zip(keys, values)]
            sql = "UPDATE persons SET " + \
                  ", ".join(columns) + \
                  " WHERE person_id = %(person_id)d"

        self.api.db.do(sql, fields)

        if commit:
            self.api.db.commit()

    def delete(self, commit = True):
        """
        Delete existing account.
        """

        assert 'person_id' in self

        # Make sure extra fields are present
        persons = Persons(self.api, [self['person_id']],
                          ['address_ids', 'key_ids'])
        assert persons
        self.update(persons.values()[0])

        # Delete all addresses
        addresses = Addresses(self.api, self['address_ids'])
        for address in addresses.values():
            address.delete(commit = False)

        # Delete all keys
        keys = Keys(self.api, self['key_ids'])
        for key in keys.values():
            key.delete(commit = False)

        # Clean up miscellaneous join tables
        for table in ['person_roles', 'person_capabilities', 'person_site',
                      'node_root_access', 'dslice03_sliceuser']:
            self.api.db.do("DELETE FROM %s" \
                           " WHERE person_id = %d" % \
                           (table, self['person_id']))

        # Mark as deleted
        self['deleted'] = True
        self.flush(commit)

class Persons(Table):
    """
    Representation of row(s) from the persons table in the
    database. Specify deleted and/or enabled to force a match on
    whether a person is deleted and/or enabled. Default is to match on
    non-deleted accounts.
    """

    def __init__(self, api, person_id_or_email_list = None, extra_fields = [], deleted = False, enabled = None):
        self.api = api

        role_max = Roles.role_max

        # N.B.: Site IDs returned may be deleted. Persons returned are
        # never deleted, but may not be enabled.
        sql = "SELECT persons.*" \
              ", roles.role_id, roles.name AS role" \
              ", person_site.site_id" \

        # N.B.: Joined IDs may be marked as deleted in their primary tables
        join_tables = {
            # extra_field: (extra_table, extra_column, join_using)
            'address_ids': ('person_address', 'address_id', 'person_id'),
            'key_ids': ('person_keys', 'key_id', 'person_id'),
            'slice_ids': ('dslice03_sliceuser', 'slice_id', 'person_id'),
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

        sql += " FROM persons" \
               " LEFT JOIN person_roles USING (person_id)" \
               " LEFT JOIN roles USING (role_id)" \
               " LEFT JOIN person_site USING (person_id)"

        if extra_tables:
            sql += " LEFT JOIN " + " LEFT JOIN ".join(extra_tables)

        # So that people with no roles have empty role_ids and roles values
        sql += " WHERE (role_id IS NULL or role_id <= %(role_max)d)"

        if deleted is not None:
            sql += " AND persons.deleted IS %(deleted)s"

        if enabled is not None:
            sql += " AND persons.enabled IS %(enabled)s"

        if person_id_or_email_list:
            # Separate the list into integers and strings
            person_ids = filter(lambda person_id: isinstance(person_id, (int, long)),
                                person_id_or_email_list)
            emails = filter(lambda email: isinstance(email, StringTypes),
                            person_id_or_email_list)
            sql += " AND (False"
            if person_ids:
                sql += " OR person_id IN (%s)" % ", ".join(map(str, person_ids))
            if emails:
                # Case insensitive e-mail address comparison
                sql += " OR lower(email) IN (%s)" % ", ".join(api.db.quote(emails)).lower()
            sql += ")"

        # The first site_id in the site_ids list is the primary site
        # of the user. See AdmGetPersonSites().
        sql += " ORDER BY person_site.is_primary DESC"

        rows = self.api.db.selectall(sql, locals())
        for row in rows:
            if self.has_key(row['person_id']):
                person = self[row['person_id']]
                person.update(row)
            else:
                self[row['person_id']] = Person(api, row)
