import re

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Debug import profile
from PLC.Table import Row, Table
from PLC.KeyTypes import KeyType, KeyTypes

class Key(Row):
    """
    Representation of a row in the keys table. To use, instantiate with a 
    dict of values. Update as you would a dict. Commit to the database 
    with sync().
    """

    table_name = 'keys'
    primary_key = 'key_id'
    fields = {
        'key_id': Parameter(int, "Key identifier"),
        'key_type': Parameter(str, "Key type"),
        'key': Parameter(str, "Key value", max = 4096),
        }

    def __init__(self, api, fields = {}):
        Row.__init__(self, fields)
	self.api = api

    def validate_key_type(self, key_type):
        if key_type not in KeyTypes(self.api):
            raise PLCInvalidArgument, "Invalid key type"
	return key_type

    def validate_key(self, key):
        key = key.strip()

	# Key must not be blacklisted
	rows = self.api.db.selectall("SELECT 1 from keys" \
				     " WHERE key = %(key)s" \
                                     " AND is_blacklisted IS True",
                                     locals())
	if rows:
            raise PLCInvalidArgument, "Key is blacklisted and cannot be used"

	return key

    def validate(self):
        # Basic validation
        Row.validate(self)

        assert 'key' in self
        key = self['key']

        if self['key_type'] == 'ssh':
            # Accept only SSH version 2 keys without options. From
            # sshd(8):
            #
            # Each protocol version 2 public key consists of: options,
            # keytype, base64 encoded key, comment.  The options field
            # is optional...The comment field is not used for anything
            # (but may be convenient for the user to identify the
            # key). For protocol version 2 the keytype is ``ssh-dss''
            # or ``ssh-rsa''.

            good_ssh_key = r'^.*(?:ssh-dss|ssh-rsa)[ ]+[A-Za-z0-9+/=]+(?: .*)?$'
            if not re.match(good_ssh_key, key, re.IGNORECASE):
                raise PLCInvalidArgument, "Invalid SSH version 2 public key"

    def blacklist(self, commit = True):
        """
	Permanently blacklist key (and all other identical keys),
	preventing it from ever being added again. Because this could
	affect multiple keys associated with multiple accounts, it
	should be admin only.        
	"""

	assert 'key_id' in self
        assert 'key' in self

        # Get all matching keys
        rows = self.api.db.selectall("SELECT key_id FROM keys WHERE key = %(key)s",
                                     self)
        key_ids = [row['key_id'] for row in rows]
        assert key_ids
        assert self['key_id'] in key_ids

        # Keep the keys in the table
        self.api.db.do("UPDATE keys SET is_blacklisted = True" \
                       " WHERE key_id IN (%s)" % ", ".join(map(str, key_ids)))

	# But disassociate them from all join tables
        for table in ['person_key']:
            self.api.db.do("DELETE FROM %s WHERE key_id IN (%s)" % \
                           (table, ", ".join(map(str, key_ids))))

        if commit:
            self.api.db.commit()

    def delete(self, commit = True):
        """
        Delete key from the database.
        """

	assert 'key_id' in self
	
	for table in ['person_key', 'keys']:
            self.api.db.do("DELETE FROM %s WHERE key_id = %d" % \
                           (table, self['key_id']))
        
        if commit:
            self.api.db.commit()

class Keys(Table):
    """
    Representation of row(s) from the keys table in the
    database.
    """

    def __init__(self, api, key_id_list = None, is_blacklisted = False):
        self.api = api
	
	sql = "SELECT %s FROM keys WHERE True" % \
              ", ".join(Key.fields)

        if is_blacklisted is not None:
            sql += " AND is_blacklisted IS %(is_blacklisted)s"            

	if key_id_list:
            sql += " AND key_id IN (%s)" %  ", ".join(map(str, key_id_list))

	rows = self.api.db.selectall(sql, locals())
	
	for row in rows:	
            self[row['key_id']] = Key(api, row)
