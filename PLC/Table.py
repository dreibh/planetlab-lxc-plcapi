class Row(dict):
    """
    Representation of a row in a database table. To use, optionally
    instantiate with a dict of values. Update as you would a
    dict. Commit to the database with flush().
    """

    # Set this to a dict of the valid columns in this table. If a column
    # name ends in 's' and the column value is set by referring to the
    # column without the 's', it is assumed that the column values
    # should be aggregated into lists. For example, if fields contains
    # the column 'role_ids' and row['role_id'] is set repeatedly to
    # different values, row['role_ids'] will contain a list of the set
    # values.
    fields = {}

    # These fields are derived from join tables and are not actually
    # in the sites table.
    join_fields = {}

    # These fields are derived from join tables and are not returned
    # by default unless specified.
    extra_fields = {}

    def __init__(self, fields):
        self.update(fields)
        
    def update(self, fields):
        for key, value in fields.iteritems():
            self.__setitem__(key, value)

    def __setitem__(self, key, value):
        """
        Magically takes care of aggregating certain variables into
        lists.
        """

        # All known keys
        all_fields = self.fields.keys() + \
                     self.join_fields.keys() + \
                     self.extra_fields.keys()

        # Aggregate into lists
        if (key + 's') in all_fields:
            key += 's'
            try:
                if value not in self[key] and value is not None:
                    self[key].append(value)
            except KeyError:
                if value is None:
                    self[key] = []
                else:
                    self[key] = [value]
            return

        elif key in all_fields:
            dict.__setitem__(self, key, value)

    def validate(self):
        """
        Validates values. Will validate a value with a custom function
        if a function named 'validate_[key]' exists.
        """

        # Validate values before committing
        # XXX Also truncate strings that are too long
        for key, value in self.iteritems():
            if value is not None and hasattr(self, 'validate_' + key):
                validate = getattr(self, 'validate_' + key)
                self[key] = validate(value)

    def flush(self, commit = True):
        """
        Flush changes back to the database.
        """

        pass

class Table(dict):
    """
    Representation of row(s) in a database table.
    """

    def flush(self, commit = True):
        """
        Flush changes back to the database.
        """

        for row in self.values():
            row.flush(commit)
