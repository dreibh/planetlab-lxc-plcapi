#
# Functions for interacting with the persons table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: Persons.py,v 1.21 2006/11/25 09:35:36 thierry Exp $
#

from types import StringTypes
from datetime import datetime
import md5
import time
from random import Random
import re
import crypt

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Table import Row, Table
from PLC.Keys import Key, Keys
import PLC.Sites

class Person(Row):
    """
    Representation of a row in the persons table. To use, optionally
    instantiate with a dict of values. Update as you would a
    dict. Commit to the database with sync().
    """

    table_name = 'persons'
    primary_key = 'person_id'
    join_tables = ['person_role', 'person_site', 'slice_person', 'person_session']
    fields = {
        'person_id': Parameter(int, "Account identifier"),
        'first_name': Parameter(str, "Given name", max = 128),
        'last_name': Parameter(str, "Surname", max = 128),
        'title': Parameter(str, "Title", max = 128, nullok = True),
        'email': Parameter(str, "Primary e-mail address", max = 254),
        'phone': Parameter(str, "Telephone number", max = 64, nullok = True),
        'url': Parameter(str, "Home page", max = 254, nullok = True),
        'bio': Parameter(str, "Biography", max = 254, nullok = True),
        'enabled': Parameter(bool, "Has been enabled"),
        'password': Parameter(str, "Account password in crypt() form", max = 254),
        'last_updated': Parameter(int, "Date and time of last update", ro = True),
        'date_created': Parameter(int, "Date and time when account was created", ro = True),
        'role_ids': Parameter([int], "List of role identifiers"),
        'roles': Parameter([str], "List of roles"),
        'site_ids': Parameter([int], "List of site identifiers"),
        'key_ids': Parameter([int], "List of key identifiers"),
        'slice_ids': Parameter([int], "List of slice identifiers"),
        'peer_id': Parameter(int, "Peer at which this slice was created", nullok = True),
        }

    # for Cache
    class_key = 'email'
    foreign_fields = ['first_name', 'last_name', 'title', 'email', 'phone', 'url',
		      'bio', 'enabled', 'password', 'last_updated', 'date_created']
    foreign_xrefs = [
        {'field' : 'key_ids',  'class': 'Key',  'table' : 'person_key' } ,
        {'field' : 'site_ids', 'class': 'Site', 'table' : 'person_site'},
#       xxx this is not handled by Cache yet
#        'role_ids': Parameter([int], "List of role identifiers"),
]

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
        for person in conflicts:
            if 'person_id' not in self or self['person_id'] != person['person_id']:
                raise PLCInvalidArgument, "E-mail address already in use"

        return email

    def validate_password(self, password):
        """
        Encrypt password if necessary before committing to the
        database.
        """

        magic = "$1$"

        if len(password) > len(magic) and \
           password[0:len(magic)] == magic:
            return password
        else:
            # Generate a somewhat unique 8 character salt string
            salt = str(time.time()) + str(Random().random())
            salt = md5.md5(salt).hexdigest()[:8] 
            return crypt.crypt(password.encode(self.api.encoding), magic + salt + "$")

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

        if role_id not in self['role_ids']:
            self.api.db.do("INSERT INTO person_role (person_id, role_id)" \
                           " VALUES(%(person_id)d, %(role_id)d)",
                           locals())

            if commit:
                self.api.db.commit()

            self['role_ids'].append(role_id)

    def remove_role(self, role_id, commit = True):
        """
        Remove role from existing account.
        """

        assert 'person_id' in self

        person_id = self['person_id']

        if role_id in self['role_ids']:
            self.api.db.do("DELETE FROM person_role" \
                           " WHERE person_id = %(person_id)d" \
                           " AND role_id = %(role_id)d",
                           locals())

            if commit:
                self.api.db.commit()

            self['role_ids'].remove(role_id)
 
    def add_key(self, key, commit = True):
        """
        Add key to existing account.
        """

        assert 'person_id' in self
        assert isinstance(key, Key)
        assert 'key_id' in key

        person_id = self['person_id']
        key_id = key['key_id']

        if key_id not in self['key_ids']:
            self.api.db.do("INSERT INTO person_key (person_id, key_id)" \
                           " VALUES(%(person_id)d, %(key_id)d)",
                           locals())

            if commit:
                self.api.db.commit()

            self['key_ids'].append(key_id)

    def remove_key(self, key, commit = True):
        """
        Remove key from existing account.
        """

        assert 'person_id' in self
        assert isinstance(key, Key)
        assert 'key_id' in key

        person_id = self['person_id']
        key_id = key['key_id']

        if key_id in self['key_ids']:
            self.api.db.do("DELETE FROM person_key" \
                           " WHERE person_id = %(person_id)d" \
                           " AND key_id = %(key_id)d",
                           locals())

            if commit:
                self.api.db.commit()

            self['key_ids'].remove(key_id)

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

    def delete(self, commit = True):
        """
        Delete existing account.
        """

        # Delete all keys
        keys = Keys(self.api, self['key_ids'])
        for key in keys:
            key.delete(commit = False)

        # Clean up miscellaneous join tables
        for table in self.join_tables:
            self.api.db.do("DELETE FROM %s WHERE person_id = %d" % \
                           (table, self['person_id']))

        # Mark as deleted
        self['deleted'] = True
        self.sync(commit)

class Persons(Table):
    """
    Representation of row(s) from the persons table in the
    database.
    """

    def __init__(self, api, person_filter = None, columns = None):
        Table.__init__(self, api, Person, columns)

        sql = "SELECT %s FROM view_persons WHERE deleted IS False" % \
              ", ".join(self.columns)

        if person_filter is not None:
            if isinstance(person_filter, (list, tuple, set)):
                # Separate the list into integers and strings
                ints = filter(lambda x: isinstance(x, (int, long)), person_filter)
                strs = filter(lambda x: isinstance(x, StringTypes), person_filter)
                person_filter = Filter(Person.fields, {'person_id': ints, 'email': strs})
                sql += " AND (%s)" % person_filter.sql(api, "OR")
            elif isinstance(person_filter, dict):
                person_filter = Filter(Person.fields, person_filter)
                sql += " AND (%s)" % person_filter.sql(api, "AND")

        self.selectall(sql)
