from types import StringTypes, IntType, LongType
import time
import calendar

from PLC.Faults import *
from PLC.Parameter import Parameter

class Row(dict):
    """
    Representation of a row in a database table. To use, optionally
    instantiate with a dict of values. Update as you would a
    dict. Commit to the database with sync().
    """

    # Set this to the name of the table that stores the row.
    table_name = None

    # Set this to the name of the primary key of the table. It is
    # assumed that the this key is a sequence if it is not set when
    # sync() is called.
    primary_key = None

    # Set this to the names of tables that reference this table's
    # primary key.
    join_tables = []

    # Set this to a dict of the valid fields of this object and their
    # types. Not all fields (e.g., joined fields) may be updated via
    # sync().
    fields = {}

    def __init__(self, api, fields = {}):
        dict.__init__(self, fields)
        self.api = api

    def validate(self):
        """
        Validates values. Will validate a value with a custom function
        if a function named 'validate_[key]' exists.
        """

        # Warn about mandatory fields
        mandatory_fields = self.api.db.fields(self.table_name, notnull = True, hasdef = False)
        for field in mandatory_fields:
            if not self.has_key(field) or self[field] is None:
                raise PLCInvalidArgument, field + " must be specified and cannot be unset in class %s"%self.__class__.__name__

        # Validate values before committing
        for key, value in self.iteritems():
            if value is not None and hasattr(self, 'validate_' + key):
                validate = getattr(self, 'validate_' + key)
                self[key] = validate(value)
	
    def separate_types(self, items):
	"""
	Separate a list of different typed objects. 
	Return a list for each type (ints, strs and dicts)
	"""
	
	if isinstance(items, (list, tuple, set)):
	    ints = filter(lambda x: isinstance(x, (int, long)), items)
	    strs = filter(lambda x: isinstance(x, StringTypes), items)
	    dicts = filter(lambda x: isinstance(x, dict), items)
	    return (ints, strs, dicts)	 	
	else:
	    raise PLCInvalidArgument, "Can only separate list types" 
	  	

    def associate(self, *args):
    	"""
	Provides a means for high lvl api calls to associate objects
        using low lvl calls.
	"""

	if len(args) < 3:
	    raise PLCInvalidArgumentCount, "auth, field, value must be specified"
	elif hasattr(self, 'associate_' + args[1]):
	    associate = getattr(self, 'associate_'+args[1])
	    associate(*args)
	else:
	    raise PLCInvalidArguemnt, "No such associate function associate_%s" % args[1]

    def validate_timestamp(self, timestamp, check_future = False):
        """
        Validates the specified GMT timestamp string (must be in
        %Y-%m-%d %H:%M:%S format) or number (seconds since UNIX epoch,
        i.e., 1970-01-01 00:00:00 GMT). If check_future is True,
        raises an exception if timestamp is not in the future. Returns
        a GMT timestamp string.
        """

        time_format = "%Y-%m-%d %H:%M:%S"

	if isinstance(timestamp, StringTypes):
	    # calendar.timegm() is the inverse of time.gmtime()
	    timestamp = calendar.timegm(time.strptime(timestamp, time_format))

        # Human readable timestamp string
	human = time.strftime(time_format, time.gmtime(timestamp))

	if check_future and timestamp < time.time():
            raise PLCInvalidArgument, "'%s' not in the future" % human

	return human

    def add_object(self, classobj, join_table, columns = None):
        """
        Returns a function that can be used to associate this object
        with another.
        """

        def add(self, obj, columns = None, commit = True):
            """
            Associate with the specified object.
            """

            # Various sanity checks
            assert isinstance(self, Row)
            assert self.primary_key in self
            assert join_table in self.join_tables
            assert isinstance(obj, classobj)
            assert isinstance(obj, Row)
            assert obj.primary_key in obj
	    assert join_table in obj.join_tables

            # By default, just insert the primary keys of each object
            # into the join table.
            if columns is None:
                columns = {self.primary_key: self[self.primary_key],
                           obj.primary_key: obj[obj.primary_key]}

            params = []
            for name, value in columns.iteritems():
                params.append(self.api.db.param(name, value))

            self.api.db.do("INSERT INTO %s (%s) VALUES(%s)" % \
                           (join_table, ", ".join(columns), ", ".join(params)),
                           columns)

            if commit:
                self.api.db.commit()
    
        return add

    add_object = classmethod(add_object)

    def remove_object(self, classobj, join_table):
        """
        Returns a function that can be used to disassociate this
        object with another.
        """

        def remove(self, obj, commit = True):
            """
            Disassociate from the specified object.
            """
    
            assert isinstance(self, Row)
            assert self.primary_key in self
            assert join_table in self.join_tables
            assert isinstance(obj, classobj)
            assert isinstance(obj, Row)
            assert obj.primary_key in obj
            assert join_table in obj.join_tables
    
            self_id = self[self.primary_key]
            obj_id = obj[obj.primary_key]
    
            self.api.db.do("DELETE FROM %s WHERE %s = %s AND %s = %s" % \
                           (join_table,
                            self.primary_key, self.api.db.param('self_id', self_id),
                            obj.primary_key, self.api.db.param('obj_id', obj_id)),
                           locals())

            if commit:
                self.api.db.commit()

        return remove

    remove_object = classmethod(remove_object)

    def db_fields(self, obj = None):
        """
        Return only those fields that can be set or updated directly
        (i.e., those fields that are in the primary table (table_name)
        for this object, and are not marked as a read-only Parameter.
        """

        if obj is None:
            obj = self

        db_fields = self.api.db.fields(self.table_name)
        return dict(filter(lambda (key, value): \
                           key in db_fields and \
                           (key not in self.fields or \
                            not isinstance(self.fields[key], Parameter) or \
                            not self.fields[key].ro),
                           obj.items()))

    def __eq__(self, y):
        """
        Compare two objects.
        """

        # Filter out fields that cannot be set or updated directly
        # (and thus would not affect equality for the purposes of
        # deciding if we should sync() or not).
        x = self.db_fields()
        y = self.db_fields(y)
        return dict.__eq__(x, y)

    def sync(self, commit = True, insert = None):
        """
        Flush changes back to the database.
        """

        # Validate all specified fields
        self.validate()

        # Filter out fields that cannot be set or updated directly
        db_fields = self.db_fields()

        # Parameterize for safety
        keys = db_fields.keys()
        values = [self.api.db.param(key, value) for (key, value) in db_fields.items()]

        # If the primary key (usually an auto-incrementing serial
        # identifier) has not been specified, or the primary key is the
        # only field in the table, or insert has been forced.
        if not self.has_key(self.primary_key) or \
           keys == [self.primary_key] or \
           insert is True:
	    
	    # If primary key id is a serial int and it isnt included, get next id
	    if self.fields[self.primary_key].type in (IntType, LongType) and \
	       self.primary_key not in self:
		pk_id = self.api.db.next_id(self.table_name, self.primary_key)
		self[self.primary_key] = pk_id
		db_fields[self.primary_key] = pk_id
		keys = db_fields.keys()
        	values = [self.api.db.param(key, value) for (key, value) in db_fields.items()]
            # Insert new row
            sql = "INSERT INTO %s (%s) VALUES (%s)" % \
                  (self.table_name, ", ".join(keys), ", ".join(values))
        else:
            # Update existing row
            columns = ["%s = %s" % (key, value) for (key, value) in zip(keys, values)]
            sql = "UPDATE %s SET " % self.table_name + \
                  ", ".join(columns) + \
                  " WHERE %s = %s" % \
                  (self.primary_key,
                   self.api.db.param(self.primary_key, self[self.primary_key]))

        self.api.db.do(sql, db_fields)

        if commit:
            self.api.db.commit()

    def delete(self, commit = True):
        """
        Delete row from its primary table, and from any tables that
        reference it.
        """

        assert self.primary_key in self

        for table in self.join_tables + [self.table_name]:
            if isinstance(table, tuple):
                key = table[1]
                table = table[0]
            else:
                key = self.primary_key

            sql = "DELETE FROM %s WHERE %s = %s" % \
                  (table, key,
                   self.api.db.param(self.primary_key, self[self.primary_key]))

            self.api.db.do(sql, self)

        if commit:
            self.api.db.commit()

class Table(list):
    """
    Representation of row(s) in a database table.
    """

    def __init__(self, api, classobj, columns = None):
        self.api = api
        self.classobj = classobj
        self.rows = {}

        if columns is None:
            columns = classobj.fields
        else:
            columns = filter(lambda x: x in classobj.fields, columns)
            if not columns:
                raise PLCInvalidArgument, "No valid return fields specified"

        self.columns = columns

    def sync(self, commit = True):
        """
        Flush changes back to the database.
        """

        for row in self:
            row.sync(commit)

    def selectall(self, sql, params = None):
        """
        Given a list of rows from the database, fill ourselves with
        Row objects.
        """

        for row in self.api.db.selectall(sql, params):
            obj = self.classobj(self.api, row)
            self.append(obj)

    def dict(self, key_field = None):
        """
        Return ourself as a dict keyed on key_field.
        """

        if key_field is None:
            key_field = self.classobj.primary_key

        return dict([(obj[key_field], obj) for obj in self])
