#
# Functions for interacting with the persons table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#

from types import StringTypes
try:
    from hashlib import md5
except ImportError:
    from md5 import md5
import time
from random import Random
import re
import crypt

from PLC.Faults import *
from PLC.Debug import log
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Table import Row, Table
from PLC.Roles import Role, Roles
from PLC.Keys import Key, Keys
from PLC.Messages import Message, Messages

class Person(Row):
    """
    Representation of a row in the persons table. To use, optionally
    instantiate with a dict of values. Update as you would a
    dict. Commit to the database with sync().
    """

    table_name = 'persons'
    primary_key = 'person_id'
    join_tables = ['person_key', 'person_role', 'person_site', 'slice_person', 'person_session', 'peer_person']
    fields = {
        'person_id': Parameter(int, "User identifier"),
        'first_name': Parameter(str, "Given name", max = 128),
        'last_name': Parameter(str, "Surname", max = 128),
        'title': Parameter(str, "Title", max = 128, nullok = True),
        'email': Parameter(str, "Primary e-mail address", max = 254),
        'phone': Parameter(str, "Telephone number", max = 64, nullok = True),
        'url': Parameter(str, "Home page", max = 254, nullok = True),
        'bio': Parameter(str, "Biography", max = 254, nullok = True),
        'enabled': Parameter(bool, "Has been enabled"),
        'password': Parameter(str, "Account password in crypt() form", max = 254),
        'verification_key': Parameter(str, "Reset password key", max = 254, nullok = True),
        'verification_expires': Parameter(int, "Date and time when verification_key expires", nullok = True),
        'last_updated': Parameter(int, "Date and time of last update", ro = True),
        'date_created': Parameter(int, "Date and time when account was created", ro = True),
        'role_ids': Parameter([int], "List of role identifiers"),
        'roles': Parameter([str], "List of roles"),
        'site_ids': Parameter([int], "List of site identifiers"),
        'key_ids': Parameter([int], "List of key identifiers"),
        'slice_ids': Parameter([int], "List of slice identifiers"),
        'peer_id': Parameter(int, "Peer to which this user belongs", nullok = True),
        'peer_person_id': Parameter(int, "Foreign user identifier at peer", nullok = True),
        'person_tag_ids' : Parameter ([int], "List of tags attached to this person"),
        }
    related_fields = {
        'roles': [Mixed(Parameter(int, "Role identifier"),
                        Parameter(str, "Role name"))],
        'sites': [Mixed(Parameter(int, "Site identifier"),
                        Parameter(str, "Site name"))],
        'keys': [Mixed(Parameter(int, "Key identifier"),
                       Filter(Key.fields))],
        'slices': [Mixed(Parameter(int, "Slice identifier"),
                         Parameter(str, "Slice name"))]
        }
    view_tags_name = "view_person_tags"
    # tags are used by the Add/Get/Update methods to expose tags
    # this is initialized here and updated by the accessors factory
    tags = { }

    def validate_email(self, email):
        """
        Validate email address. Stolen from Mailman.
        """
        email = email.lower()
        invalid_email = PLCInvalidArgument("Invalid e-mail address")

        if not email:
            raise invalid_email

        email_re = re.compile('\A[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9._\-]+\.[a-zA-Z]+\Z')
        if not email_re.match(email):
            raise invalid_email

        # check only against users on the same peer
        if 'peer_id' in self:
            namespace_peer_id = self['peer_id']
        else:
            namespace_peer_id = None

        conflicts = Persons(self.api, {'email':email,'peer_id':namespace_peer_id})

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
            salt = md5(salt).hexdigest()[:8]
            return crypt.crypt(password.encode(self.api.encoding), magic + salt + "$")

    validate_date_created = Row.validate_timestamp
    validate_last_updated = Row.validate_timestamp
    validate_verification_expires = Row.validate_timestamp

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
                # non-admin users cannot update a person who is neither a PI or ADMIN
                return (not set(['pi','admin']).intersection(person['roles']))

        return False

    def can_view(self, person):
        """
        Returns true if we can view the specified person. We can
        view a person if:

        1. We are the person.
        2. We are an admin.
        3. We are a PI or Tech and the person is at one of our sites.
        """

        assert isinstance(person, Person)

        if self.can_update(person):
            return True

        # pis and techs can see all people on their site
        if set(['pi','tech']).intersection(self['roles']):
            if set(self['site_ids']).intersection(person['site_ids']):
                return True

        return False

    add_role = Row.add_object(Role, 'person_role')
    remove_role = Row.remove_object(Role, 'person_role')

    add_key = Row.add_object(Key, 'person_key')
    remove_key = Row.remove_object(Key, 'person_key')

    def set_primary_site(self, site, commit = True):
        """
        Set the primary site for an existing user.
        """

        assert 'person_id' in self
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

    def update_last_updated(self, commit = True):
        """
        Update last_updated field with current time
        """

        assert 'person_id' in self
        assert self.table_name

        self.api.db.do("UPDATE %s SET last_updated = CURRENT_TIMESTAMP " % (self.table_name) + \
                       " where person_id = %d" % (self['person_id']) )
        self.sync(commit)

    def associate_roles(self, auth, field, value):
        """
        Adds roles found in value list to this person (using AddRoleToPerson).
        Deletes roles not found in value list from this person (using DeleteRoleFromPerson).
        """

        assert 'role_ids' in self
        assert 'person_id' in self
        assert isinstance(value, list)

        (role_ids, role_names) = self.separate_types(value)[0:2]

        # Translate roles into role_ids
        if role_names:
            roles = Roles(self.api, role_names).dict('role_id')
            role_ids += roles.keys()

        # Add new ids, remove stale ids
        if self['role_ids'] != role_ids:
            from PLC.Methods.AddRoleToPerson import AddRoleToPerson
            from PLC.Methods.DeleteRoleFromPerson import DeleteRoleFromPerson
            new_roles = set(role_ids).difference(self['role_ids'])
            stale_roles = set(self['role_ids']).difference(role_ids)

            for new_role in new_roles:
                AddRoleToPerson.__call__(AddRoleToPerson(self.api), auth, new_role, self['person_id'])
            for stale_role in stale_roles:
                DeleteRoleFromPerson.__call__(DeleteRoleFromPerson(self.api), auth, stale_role, self['person_id'])


    def associate_sites(self, auth, field, value):
        """
        Adds person to sites found in value list (using AddPersonToSite).
        Deletes person from site not found in value list (using DeletePersonFromSite).
        """

        from PLC.Sites import Sites

        assert 'site_ids' in self
        assert 'person_id' in self
        assert isinstance(value, list)

        (site_ids, site_names) = self.separate_types(value)[0:2]

        # Translate roles into role_ids
        if site_names:
            sites = Sites(self.api, site_names, ['site_id']).dict('site_id')
            site_ids += sites.keys()

        # Add new ids, remove stale ids
        if self['site_ids'] != site_ids:
            from PLC.Methods.AddPersonToSite import AddPersonToSite
            from PLC.Methods.DeletePersonFromSite import DeletePersonFromSite
            new_sites = set(site_ids).difference(self['site_ids'])
            stale_sites = set(self['site_ids']).difference(site_ids)

            for new_site in new_sites:
                AddPersonToSite.__call__(AddPersonToSite(self.api), auth, self['person_id'], new_site)
            for stale_site in stale_sites:
                DeletePersonFromSite.__call__(DeletePersonFromSite(self.api), auth, self['person_id'], stale_site)


    def associate_keys(self, auth, field, value):
        """
        Deletes key_ids not found in value list (using DeleteKey).
        Adds key if key_fields w/o key_id is found (using AddPersonKey).
        Updates key if key_fields w/ key_id is found (using UpdateKey).
        """
        assert 'key_ids' in self
        assert 'person_id' in self
        assert isinstance(value, list)

        (key_ids, blank, keys) = self.separate_types(value)

        if self['key_ids'] != key_ids:
            from PLC.Methods.DeleteKey import DeleteKey
            stale_keys = set(self['key_ids']).difference(key_ids)

            for stale_key in stale_keys:
                DeleteKey.__call__(DeleteKey(self.api), auth, stale_key)

        if keys:
            from PLC.Methods.AddPersonKey import AddPersonKey
            from PLC.Methods.UpdateKey import UpdateKey
            updated_keys = filter(lambda key: 'key_id' in key, keys)
            added_keys = filter(lambda key: 'key_id' not in key, keys)

            for key in added_keys:
                AddPersonKey.__call__(AddPersonKey(self.api), auth, self['person_id'], key)
            for key in updated_keys:
                key_id = key.pop('key_id')
                UpdateKey.__call__(UpdateKey(self.api), auth, key_id, key)


    def associate_slices(self, auth, field, value):
        """
        Adds person to slices found in value list (using AddPersonToSlice).
        Deletes person from slices found in value list (using DeletePersonFromSlice).
        """

        from PLC.Slices import Slices

        assert 'slice_ids' in self
        assert 'person_id' in self
        assert isinstance(value, list)

        (slice_ids, slice_names) = self.separate_types(value)[0:2]

        # Translate roles into role_ids
        if slice_names:
            slices = Slices(self.api, slice_names, ['slice_id']).dict('slice_id')
            slice_ids += slices.keys()

        # Add new ids, remove stale ids
        if self['slice_ids'] != slice_ids:
            from PLC.Methods.AddPersonToSlice import AddPersonToSlice
            from PLC.Methods.DeletePersonFromSlice import DeletePersonFromSlice
            new_slices = set(slice_ids).difference(self['slice_ids'])
            stale_slices = set(self['slice_ids']).difference(slice_ids)

            for new_slice in new_slices:
                AddPersonToSlice.__call__(AddPersonToSlice(self.api), auth, self['person_id'], new_slice)
            for stale_slice in stale_slices:
                DeletePersonFromSlice.__call__(DeletePersonFromSlice(self.api), auth, self['person_id'], stale_slice)


    def delete(self, commit = True):
        """
        Delete existing user.
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

        # delete will fail if timestamp fields aren't validated, so lets remove them
        for field in ['verification_expires', 'date_created', 'last_updated']:
            if field in self:
                self.pop(field)

        # don't validate, so duplicates can be consistently removed
        self.sync(commit, validate=False)

class Persons(Table):
    """
    Representation of row(s) from the persons table in the
    database.
    """

    def __init__(self, api, person_filter = None, columns = None):
        Table.__init__(self, api, Person, columns)

        view = "view_persons"
        for tagname in self.tag_columns:
            view= "%s left join %s using (%s)"%(view,Person.tagvalue_view_name(tagname),
                                                Person.primary_key)

        sql = "SELECT %s FROM %s WHERE deleted IS False" % \
            (", ".join(self.columns.keys()+self.tag_columns.keys()),view)

        if person_filter is not None:
            if isinstance(person_filter, (list, tuple, set)):
                # Separate the list into integers and strings
                ints = filter(lambda x: isinstance(x, (int, long)), person_filter)
                strs = filter(lambda x: isinstance(x, StringTypes), person_filter)
                person_filter = Filter(Person.fields, {'person_id': ints, 'email': strs})
                sql += " AND (%s) %s" % person_filter.sql(api, "OR")
            elif isinstance(person_filter, dict):
                person_filter = Filter(Person.fields, person_filter)
                sql += " AND (%s) %s" % person_filter.sql(api, "AND")
            elif isinstance (person_filter, StringTypes):
                person_filter = Filter(Person.fields, {'email':person_filter})
                sql += " AND (%s) %s" % person_filter.sql(api, "AND")
            elif isinstance (person_filter, (int, long)):
                person_filter = Filter(Person.fields, {'person_id':person_filter})
                sql += " AND (%s) %s" % person_filter.sql(api, "AND")
            else:
                raise PLCInvalidArgument, "Wrong person filter %r"%person_filter

        self.selectall(sql)
