from types import StringTypes
import time

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Debug import profile
from PLC.Table import Row, Table
from PLC.SliceInstantiations import SliceInstantiations
import PLC.Persons

class Slice(Row):
    """
    Representation of a row in the slices table. To use, optionally
    instantiate with a dict of values. Update as you would a
    dict. Commit to the database with sync().To use, instantiate
    with a dict of values.
    """

    fields = {
        'slice_id': Parameter(int, "Slice type"),
        'site_id': Parameter(int, "Identifier of the site to which this slice belongs"),
        'name': Parameter(str, "Slice name", max = 32),
        'instantiation': Parameter(str, "Slice instantiation state"),
        'url': Parameter(str, "URL further describing this slice", max = 254),
        'description': Parameter(str, "Slice description", max = 2048),
        'max_nodes': Parameter(int, "Maximum number of nodes that can be assigned to this slice"),
        'creator_person_id': Parameter(int, "Identifier of the account that created this slice"),
        'created': Parameter(int, "Date and time when slice was created, in seconds since UNIX epoch"),
        'expires': Parameter(int, "Date and time when slice expires, in seconds since UNIX epoch"),
        'node_ids': Parameter([int], "List of nodes in this slice"),
        'person_ids': Parameter([int], "List of accounts that can use this slice"),
        'attribute_ids': Parameter([int], "List of slice attributes"),
        }

    def __init__(self, api, fields):
        Row.__init__(self, fields)
        self.api = api

    def validate_name(self, name):
        # N.B.: Responsibility of the caller to ensure that login_base
        # portion of the slice name corresponds to a valid site, if
        # desired.
        conflicts = Slices(self.api, [name])
        for slice_id, slice in conflicts.iteritems():
            if 'slice_id' not in self or self['slice_id'] != slice_id:
                raise PLCInvalidArgument, "Slice name already in use"

        return name

    def validate_instantiation(self, instantiation):
        instantiations = SliceInstantiations(self.api)
        if instantiation not in instantiations:
            raise PLCInvalidArgument, "No such instantiation state"

        return state

    def validate_expires(self, expires):
        # N.B.: Responsibility of the caller to ensure that expires is
        # not too far into the future.
        if expires < time.time():
            raise PLCInvalidArgument, "Expiration date must be in the future"

        return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(expires))

    def validate_creator_person_id(self, person_id):
        persons = PLC.Persons.Persons(self.api, [person_id])
        if not persons:
            raise PLCInvalidArgument, "Invalid creator"

        return person_id

    def sync(self, commit = True):
        """
        Flush changes back to the database.
        """

        try:
            if not self['name']:
                raise KeyError
        except KeyError:
            raise PLCInvalidArgument, "Slice name must be specified"

        self.validate()

        # Fetch a new slice_id if necessary
        if 'slice_id' not in self:
            # N.B.: Responsibility of the caller to ensure that
            # max_slices is not exceeded.
            rows = self.api.db.selectall("SELECT NEXTVAL('slices_slice_id_seq') AS slice_id")
            if not rows:
                raise PLCDBError, "Unable to fetch new slice_id"
            self['slice_id'] = rows[0]['slice_id']
            insert = True
        else:
            insert = False

        # Filter out fields that cannot be set or updated directly
        slices_fields = self.api.db.fields('slices')
        fields = dict(filter(lambda (key, value): key in slices_fields,
                             self.items()))
        for ro_field in 'created',:
            if ro_field in fields:
                del fields[ro_field]

        # Parameterize for safety
        keys = fields.keys()
        values = [self.api.db.param(key, value) for (key, value) in fields.items()]

        if insert:
            # Insert new row in slices table
            sql = "INSERT INTO slices (%s) VALUES (%s)" % \
                  (", ".join(keys), ", ".join(values))
        else:
            # Update existing row in slices table
            columns = ["%s = %s" % (key, value) for (key, value) in zip(keys, values)]
            sql = "UPDATE slices SET " + \
                  ", ".join(columns) + \
                  " WHERE slice_id = %(slice_id)d"

        self.api.db.do(sql, fields)

        if commit:
            self.api.db.commit()

    def delete(self, commit = True):
        """
        Delete existing slice.
        """

        assert 'slice_id' in self

        # Clean up miscellaneous join tables
        for table in ['slice_node', 'slice_person', 'slice_attribute']:
            self.api.db.do("DELETE FROM %s" \
                           " WHERE slice_id = %d" % \
                           (table, self['slice_id']), self)

        # Mark as deleted
        self['is_deleted'] = True
        self.sync(commit)

class Slices(Table):
    """
    Representation of row(s) from the slices table in the
    database.
    """

    def __init__(self, api, slice_id_or_name_list = None, fields = Slice.fields):
        self.api = api

        sql = "SELECT %s FROM view_slices WHERE is_deleted IS False" % \
              ", ".join(fields)

        if slice_id_or_name_list:
            # Separate the list into integers and strings
            slice_ids = filter(lambda slice_id: isinstance(slice_id, (int, long)),
                               slice_id_or_name_list)
            names = filter(lambda name: isinstance(name, StringTypes),
                           slice_id_or_name_list)
            sql += " AND (False"
            if slice_ids:
                sql += " OR slice_id IN (%s)" % ", ".join(map(str, slice_ids))
            if names:
                sql += " OR name IN (%s)" % ", ".join(api.db.quote(names))
            sql += ")"

        rows = self.api.db.selectall(sql)

        for row in rows:
            self[row['slice_id']] = slice = Slice(api, row)
            for aggregate in 'person_ids', 'slice_ids', 'attribute_ids':
                if not slice.has_key(aggregate) or slice[aggregate] is None:
                    slice[aggregate] = []
                else:
                    slice[aggregate] = map(int, slice[aggregate].split(','))
