#
# Functions for interacting with the persons table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: Persons.py,v 1.3 2006/09/08 19:45:46 mlhuang Exp $
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
from PLC.Debug import profile
from PLC.Table import Row, Table
from PLC.Roles import Roles
from PLC.Addresses import Address, Addresses
from PLC.Keys import Key, Keys
import PLC.Sites

class Person(Row):
    """
    Representation of a row in the persons table. To use, optionally
    instantiate with a dict of values. Update as you would a
    dict. Commit to the database with sync().
    """

    fields = {
        'person_id': Parameter(int, "Account identifier"),
        'first_name': Parameter(str, "Given name", max = 128),
        'last_name': Parameter(str, "Surname", max = 128),
        'title': Parameter(str, "Title", max = 128),
        'email': Parameter(str, "Primary e-mail address", max = 254),
        'phone': Parameter(str, "Telephone number", max = 64),
        'url': Parameter(str, "Home page", max = 254),
        'bio': Parameter(str, "Biography", max = 254),
        'enabled': Parameter(bool, "Has been enabled"),
        'deleted': Parameter(bool, "Has been deleted"),
        'password': Parameter(str, "Account password in crypt() form", max = 254),
        'last_updated': Parameter(str, "Date and time of last update"),
        'date_created': Parameter(str, "Date and time when account was created"),
        'role_ids': Parameter([int], "List of role identifiers"),
        'roles': Parameter([str], "List of roles"),
        'site_ids': Parameter([int], "List of site identifiers"),
        'address_ids': Parameter([int], "List of address identifiers"),
        'key_ids': Parameter([int], "List of key identifiers"),
        # 'slice_ids': Parameter([int], "List of slice identifiers"),
        }

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
        self.api.db.do("INSERT INTO person_role (person_id, role_id)" \
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
        self.api.db.do("DELETE FROM person_role" \
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

    def sync(self, commit = True):
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
        persons_fields = self.api.db.fields('persons')
        fields = dict(filter(lambda (key, value): key in persons_fields,
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

        # Delete all addresses
        addresses = Addresses(self.api, self['address_ids'])
        for address in addresses.values():
            address.delete(commit = False)

        # Delete all keys
        keys = Keys(self.api, self['key_ids'])
        for key in keys.values():
            key.delete(commit = False)

        # Clean up miscellaneous join tables
        for table in ['person_role', 'person_site']:
            self.api.db.do("DELETE FROM %s" \
                           " WHERE person_id = %d" % \
                           (table, self['person_id']))

        # Mark as deleted
        self['deleted'] = True
        self.sync(commit)

class Persons(Table):
    """
    Representation of row(s) from the persons table in the
    database. Specify deleted and/or enabled to force a match on
    whether a person is deleted and/or enabled. Default is to match on
    non-deleted accounts.
    """

    def __init__(self, api, person_id_or_email_list = None, fields = Person.fields, deleted = False, enabled = None):
        self.api = api

        sql = "SELECT %s FROM view_persons WHERE TRUE" % \
              ", ".join(fields)

        if deleted is not None:
            sql += " AND deleted IS %(deleted)s"

        if enabled is not None:
            sql += " AND enabled IS %(enabled)s"

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

        rows = self.api.db.selectall(sql, locals())

        for row in rows:
            self[row['person_id']] = person = Person(api, row)
            for aggregate in 'role_ids', 'roles', 'site_ids', 'address_ids', 'key_ids':
                if not person.has_key(aggregate) or person[aggregate] is None:
                    person[aggregate] = []
                else:
                    elements = person[aggregate].split(',')
                    try:
                        person[aggregate] = map(int, elements)
                    except ValueError:
                        person[aggregate] = elements
