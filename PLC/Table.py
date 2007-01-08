from types import StringTypes
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

    time_format = "%Y-%m-%d %H:%M:%S"
    def validate_timestamp (self, timestamp, check_future=False):
	# in case we try to sync the same object twice
	if isinstance(timestamp, StringTypes):
	    # calendar.timegm is the inverse of time.gmtime, in that it computes in UTC
	    # surprisingly enough, no other method in the time module behaves this way
            # this method is documented in the time module's documentation
	    timestamp = calendar.timegm (time.strptime (timestamp,Row.time_format))
	human = time.strftime (Row.time_format, time.gmtime(timestamp))
	if check_future and (timestamp < time.time()):
            raise PLCInvalidArgument, "%s: date must be in the future"%human
	return human

    @classmethod
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
    
    @classmethod
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

        if not self.has_key(self.primary_key):
            self[self.primary_key] = self.api.db.last_insert_id(self.table_name, self.primary_key)

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
