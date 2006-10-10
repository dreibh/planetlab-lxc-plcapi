from types import StringTypes

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Debug import profile
from PLC.Table import Row, Table
import PLC
class Key(Row):
    """
    Representation of a row in the keys table. To use, instantiate with a 
    dict of values. Update as you would a dict. Commit to the database 
    with sync().
    """
    table_name = 'keys'
    primary_key = 'key_id'
    fields = {
        'key_id': Parameter(int, "Key type"),
        'key_type': Parameter(str, "Key type"),
        'key': Parameter(str, "Key value"),
        'is_blacklisted': Parameter(str, "Key has been blacklisted and is forever unusable"),
	'person_id': Parameter(int, "Identifier of the account that created this key"),
	'is_primary': Parameter(bool, "Is the primary key for this account")
        }

    def __init__(self, api, fields):
        Row.__init__(self, fields)
	self.api = api
        
   
    def validate_key_type(self, key_type):
	# 1. ssh is the only supported key type
	if not key_type or not key_type in ['ssh']:
		raise PLCInvalidArgument, "Invalid key type"

	return key_type

    def validate_key(self, key):
	# 1. key must not be blacklisted

	# Remove leading and trailing spaces
	key = key.strip()
	# Make sure key is not blank 
	if not len(key) > 0:
                raise PLCInvalidArgument, "Invalid key"

	rows = self.api.db.selectall("SELECT is_blacklisted from keys" \
				     " WHERE key = '%s'" % key)
	if rows:
		raise PLCInvalidArgument, "Key is blacklisted"	
	return key
    
    def add_person(self, person, commit = True):
	"""
	Associate key with person
	"""
	
	assert 'key_id' in self
	assert isinstance(person, PLC.Persons.Person)
	assert 'person_id' in person

	person_id = person['person_id']
	key_id = self['key_id']
	
	if not 'person_id' in self:
		assert key_id not in person['key_ids']
		
		self.api.db.do("INSERT INTO person_key (person_id, key_id)" \
			       " VALUES (%d, %d)" % (person_id, key_id) )
		if commit:
			self.api.db.commit()

		self['person_id'] = person_id
		person['key_id'] = key_id 

    def set_primary_key(self, person, commit = True):
	"""
	Set the primary key for a person
	"""

	assert 'key_id' in self
        assert isinstance(person, PLC.Persons.Person)
        assert 'person_id' in person

	person_id = person['person_id']
        key_id = self['key_id']
	assert person_id in [self['person_id']]

	self.api.db.do("UPDATE person_key SET is_primary = False" \
		       " WHERE person_id = %d " % person_id)
	self.api.db.do("UPDATE person_key SET is_primary = True" \
		       " WHERE person_id = %d AND key_id = %d" \
		       % (person_id, key_id) )

	if commit:
		self.api.db.commit()
	
	self['is_primary'] = True
	
    def delete(self, commit = True):
        """
	Delete key from the database
	"""
	assert 'key_id' in self
	
	for table in ['person_key', 'keys']:
		self.api.db.do("DELETE FROM %s WHERE key_id = %d" % \
		 (table, self['key_id']), self)

	if commit:
       		self.api.db.commit()

class Keys(Table):
    """
    Representation of row(s) from the keys table in the
    database.
    """

    def __init__(self, api, key_id_list = None):
        self.api = api
	
	sql = "SELECT %s FROM keys LEFT JOIN person_key USING (%s) " % \
		(", ".join(Key.fields), Key.primary_key)
	
	if key_id_list:
		sql += " WHERE key_id IN (%s)" %  ", ".join(map(str, key_id_list))

	rows = self.api.db.selectall(sql)
	
	for row in rows:	
		self[row['key_id']] = Key(api, row)
		
  
