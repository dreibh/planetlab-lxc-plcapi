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
                raise PLCInvalidArgument, field + " must be specified and cannot be unset"

        # Validate values before committing
        for key, value in self.iteritems():
            if value is not None and hasattr(self, 'validate_' + key):
                validate = getattr(self, 'validate_' + key)
                self[key] = validate(value)

    def sync(self, commit = True, insert = None):
        """
        Flush changes back to the database.
        """

        # Validate all specified fields
        self.validate()

        # Filter out fields that cannot be set or updated directly
        all_fields = self.api.db.fields(self.table_name)
        fields = dict(filter(lambda (key, value): \
                             key in all_fields and \
                             (key not in self.fields or \
                              not isinstance(self.fields[key], Parameter) or \
                              not self.fields[key].ro),
                             self.items()))

        # Parameterize for safety
        keys = fields.keys()
        values = [self.api.db.param(key, value) for (key, value) in fields.items()]

        # If the primary key (usually an auto-incrementing serial
        # identifier) has not been specified, or the primary key is the
        # only field in the table, or insert has been forced.
        if not self.has_key(self.primary_key) or \
           all_fields == [self.primary_key] or \
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

        self.api.db.do(sql, fields)

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

class Table(dict):
    """
    Representation of row(s) in a database table.
    """

    def __init__(self, api, row):
        self.api = api
        self.row = row

    def sync(self, commit = True):
        """
        Flush changes back to the database.
        """

        for row in self.values():
            row.sync(commit)

    def selectall(self, sql, params = None):
        """
        Given a list of rows from the database, fill ourselves with
        Row objects keyed on the primary key defined by the Row class
        we were initialized with.
        """

        for row in self.api.db.selectall(sql, params):
            self[row[self.row.primary_key]] = self.row(self.api, row)
