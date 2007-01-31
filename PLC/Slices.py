from types import StringTypes
import time
import re

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Debug import profile
from PLC.Table import Row, Table
from PLC.SliceInstantiations import SliceInstantiation, SliceInstantiations
from PLC.Nodes import Node, Nodes
from PLC.Persons import Person, Persons

class Slice(Row):
    """
    Representation of a row in the slices table. To use, optionally
    instantiate with a dict of values. Update as you would a
    dict. Commit to the database with sync().To use, instantiate
    with a dict of values.
    """

    table_name = 'slices'
    primary_key = 'slice_id'
    join_tables = ['slice_node', 'slice_person', 'slice_attribute', 'peer_slice']
    fields = {
        'slice_id': Parameter(int, "Slice identifier"),
        'site_id': Parameter(int, "Identifier of the site to which this slice belongs"),
        'name': Parameter(str, "Slice name", max = 32),
        'instantiation': Parameter(str, "Slice instantiation state"),
        'url': Parameter(str, "URL further describing this slice", max = 254, nullok = True),
        'description': Parameter(str, "Slice description", max = 2048, nullok = True),
        'max_nodes': Parameter(int, "Maximum number of nodes that can be assigned to this slice"),
        'creator_person_id': Parameter(int, "Identifier of the account that created this slice"),
        'created': Parameter(int, "Date and time when slice was created, in seconds since UNIX epoch", ro = True),
        'expires': Parameter(int, "Date and time when slice expires, in seconds since UNIX epoch"),
        'node_ids': Parameter([int], "List of nodes in this slice", ro = True),
        'person_ids': Parameter([int], "List of accounts that can use this slice", ro = True),
        'slice_attribute_ids': Parameter([int], "List of slice attributes", ro = True),
        'peer_id': Parameter(int, "Peer to which this slice belongs", nullok = True),
        'peer_slice_id': Parameter(int, "Foreign slice identifier at peer", nullok = True),
        }
    # for Cache
    class_key = 'name'
    foreign_fields = ['instantiation', 'url', 'description', 'max_nodes', 'expires']
    foreign_xrefs = [
        {'field': 'node_ids' ,         'class': 'Node',   'table': 'slice_node' },
	{'field': 'person_ids',        'class': 'Person', 'table': 'slice_person'},
	{'field': 'creator_person_id', 'class': 'Person', 'table': 'unused-on-direct-refs'},
        {'field': 'site_id',           'class': 'Site',   'table': 'unused-on-direct-refs'},
    ]
    # forget about this one, it is read-only anyway
    # handling it causes Cache to re-sync all over again 
    # 'created'

    def validate_name(self, name):
        # N.B.: Responsibility of the caller to ensure that login_base
        # portion of the slice name corresponds to a valid site, if
        # desired.

        # 1. Lowercase.
        # 2. Begins with login_base (letters or numbers).
        # 3. Then single underscore after login_base.
        # 4. Then letters, numbers, or underscores.
        good_name = r'^[a-z0-9]+_[a-z0-9_]+$'
        if not name or \
           not re.match(good_name, name):
            raise PLCInvalidArgument, "Invalid slice name"

        conflicts = Slices(self.api, [name])
        for slice in conflicts:
            if 'slice_id' not in self or self['slice_id'] != slice['slice_id']:
                raise PLCInvalidArgument, "Slice name already in use, %s"%name

        return name

    def validate_instantiation(self, instantiation):
        instantiations = [row['instantiation'] for row in SliceInstantiations(self.api)]
        if instantiation not in instantiations:
            raise PLCInvalidArgument, "No such instantiation state"

        return instantiation

    validate_created = Row.validate_timestamp

    def validate_expires(self, expires):
        # N.B.: Responsibility of the caller to ensure that expires is
        # not too far into the future.
        check_future = not ('is_deleted' in self and self['is_deleted'])
        return Row.validate_timestamp(self, expires, check_future = check_future)

    add_person = Row.add_object(Person, 'slice_person')
    remove_person = Row.remove_object(Person, 'slice_person')

    add_node = Row.add_object(Node, 'slice_node')
    remove_node = Row.remove_object(Node, 'slice_node')

    def sync(self, commit = True):
        """
        Add or update a slice.
        """

        # Before a new slice is added, delete expired slices
        if 'slice_id' not in self:
            expired = Slices(self.api, expires = -int(time.time()))
            for slice in expired:
                slice.delete(commit)

        Row.sync(self, commit)

    def delete(self, commit = True):
        """
        Delete existing slice.
        """

        assert 'slice_id' in self

        # Clean up miscellaneous join tables
        for table in self.join_tables:
            self.api.db.do("DELETE FROM %s WHERE slice_id = %d" % \
                           (table, self['slice_id']))

        # Mark as deleted
        self['is_deleted'] = True
        self.sync(commit)

class Slices(Table):
    """
    Representation of row(s) from the slices table in the
    database.
    """

    def __init__(self, api, slice_filter = None, columns = None, expires = int(time.time())):
        Table.__init__(self, api, Slice, columns)

        sql = "SELECT %s FROM view_slices WHERE is_deleted IS False" % \
              ", ".join(self.columns)

        if expires is not None:
            if expires >= 0:
                sql += " AND expires > %(expires)d"
            else:
                expires = -expires
                sql += " AND expires < %(expires)d"

        if slice_filter is not None:
            if isinstance(slice_filter, (list, tuple, set)):
                # Separate the list into integers and strings
                ints = filter(lambda x: isinstance(x, (int, long)), slice_filter)
                strs = filter(lambda x: isinstance(x, StringTypes), slice_filter)
                slice_filter = Filter(Slice.fields, {'slice_id': ints, 'name': strs})
                sql += " AND (%s)" % slice_filter.sql(api, "OR")
            elif isinstance(slice_filter, dict):
                slice_filter = Filter(Slice.fields, slice_filter)
                sql += " AND (%s)" % slice_filter.sql(api, "AND")

        self.selectall(sql, locals())
