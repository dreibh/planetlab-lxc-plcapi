#
# Functions for interacting with the persons table in the database
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: Persons.py,v 1.35 2007/03/29 13:17:09 tmack Exp $
#

from types import StringTypes
from datetime import datetime
import md5
import time
from random import Random
import re
import crypt

from PLC.Faults import *
from PLC.Debug import log
from PLC.Parameter import Parameter
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
        }

    # for Cache
    class_key = 'email'
    foreign_fields = ['first_name', 'last_name', 'title', 'email', 'phone', 'url',
		      'bio', 'enabled', 'password', ]
    # forget about these ones, they are read-only anyway
    # handling them causes Cache to re-sync all over again 
    # 'last_updated', 'date_created'
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

        # This means local, unqualified addresses, are not allowed
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
        self.sync(commit)

class Persons(Table):
    """
    Representation of row(s) from the persons table in the
    database.
    """

    def __init__(self, api, person_filter = None, columns = None):
        Table.__init__(self, api, Person, columns)
        #sql = "SELECT %s FROM view_persons WHERE deleted IS False" % \
        #      ", ".join(self.columns)
	foreign_fields = {'role_ids': ('role_id', 'person_role'),
			  'roles': ('name', 'roles'),
                          'site_ids': ('site_id', 'person_site'),
                          'key_ids': ('key_id', 'person_key'),
                          'slice_ids': ('slice_id', 'slice_person')
                          }
	foreign_keys = {}
	db_fields = filter(lambda field: field not in foreign_fields.keys(), Person.fields.keys())
	all_fields = db_fields + [value[0] for value in foreign_fields.values()]
	fields = []
	_select = "SELECT "
	_from = " FROM persons "
	_join = " LEFT JOIN peer_person USING (person_id) "  
	_where = " WHERE deleted IS False "

	if not columns:
	    # include all columns	
	    fields = all_fields
	    tables = [value[1] for value in foreign_fields.values()]
	    tables.sort()
	    for key in foreign_fields.keys():
		foreign_keys[foreign_fields[key][0]] = key  
	    for table in tables:
		if table in ['roles']:
		    _join += " LEFT JOIN roles USING(role_id) "
		else:	
	    	    _join += " LEFT JOIN %s USING (person_id) " % (table)
	else: 
	    tables = set()
	    columns = filter(lambda column: column in db_fields+foreign_fields.keys(), columns)
	    columns.sort()
	    for column in columns: 
	        if column in foreign_fields.keys():
		    (field, table) = foreign_fields[column]
		    foreign_keys[field] = column
		    fields += [field]
		    tables.add(table)
		    if column in ['roles']:
			_join += " LEFT JOIN roles USING(role_id) "
		    else:
		    	_join += " LEFT JOIN %s USING (person_id)" % \
				(foreign_fields[column][1])
		
		else:
		    fields += [column]	
	
	# postgres will return timestamps as datetime objects. 
	# XMLPRC cannot marshal datetime so convert to int
	timestamps = ['date_created', 'last_updated', 'verification_expires']
	for field in fields:
	    if field in timestamps:
		fields[fields.index(field)] = \
		 "CAST(date_part('epoch', %s) AS bigint) AS %s" % (field, field)

	_select += ", ".join(fields)
	sql = _select + _from + _join + _where

	# deal with filter			
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

	# aggregate data
	all_persons = {}
	for row in self.api.db.selectall(sql):
	    person_id = row['person_id']

	    if all_persons.has_key(person_id):
		for (key, key_list) in foreign_keys.items():
		    data = row.pop(key)
		    row[key_list] = [data]
		    if data and data not in all_persons[person_id][key_list]:
		    	all_persons[person_id][key_list].append(data)
            else:
		for key in foreign_keys.keys():
                    value = row.pop(key)
		    if value:	
                    	row[foreign_keys[key]] = [value]
		    else:
			row[foreign_keys[key]] = []
		if row: 
            	    all_persons[person_id] = row
            	
	# populate self
	for row in all_persons.values():
	    obj = self.classobj(self.api, row)
            self.append(obj)

