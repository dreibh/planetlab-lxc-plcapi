class Row(dict):
    """
    Representation of a row in a database table. To use, optionally
    instantiate with a dict of values. Update as you would a
    dict. Commit to the database with sync().
    """

    # Set this to a dict of the valid fields of this object. Not all
    # fields (e.g., joined fields) may be updated via sync().
    fields = {}

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

        if key in self.fields:
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

    def sync(self, commit = True):
        """
        Flush changes back to the database.
        """

        pass

class Table(dict):
    """
    Representation of row(s) in a database table.
    """

    def sync(self, commit = True):
        """
        Flush changes back to the database.
        """

        for row in self.values():
            row.sync(commit)
