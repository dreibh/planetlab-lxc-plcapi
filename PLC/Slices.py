from types import StringTypes
import time
import re

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Debug import profile
from PLC.Table import Row, Table
from PLC.SliceInstantiations import SliceInstantiations
from PLC.Nodes import Node, Nodes
import PLC.Persons

class Slice(Row):
    """
    Representation of a row in the slices table. To use, optionally
    instantiate with a dict of values. Update as you would a
    dict. Commit to the database with sync().To use, instantiate
    with a dict of values.
    """

    table_name = 'slices'
    primary_key = 'slice_id'
    fields = {
        'slice_id': Parameter(int, "Slice identifier"),
        'site_id': Parameter(int, "Identifier of the site to which this slice belongs"),
        'name': Parameter(str, "Slice name", max = 32),
        'instantiation': Parameter(str, "Slice instantiation state"),
        'url': Parameter(str, "URL further describing this slice", max = 254),
        'description': Parameter(str, "Slice description", max = 2048),
        'max_nodes': Parameter(int, "Maximum number of nodes that can be assigned to this slice"),
        'creator_person_id': Parameter(int, "Identifier of the account that created this slice"),
        'created': Parameter(int, "Date and time when slice was created, in seconds since UNIX epoch", ro = True),
        'expires': Parameter(int, "Date and time when slice expires, in seconds since UNIX epoch"),
        'node_ids': Parameter([int], "List of nodes in this slice", ro = True),
        'person_ids': Parameter([int], "List of accounts that can use this slice", ro = True),
        'slice_attribute_ids': Parameter([int], "List of slice attributes", ro = True),
        }

    def validate_name(self, name):
        # N.B.: Responsibility of the caller to ensure that login_base
        # portion of the slice name corresponds to a valid site, if
        # desired.

        # 1. Lowercase.
        # 2. Begins with login_base (only letters).
        # 3. Then single underscore after login_base.
        # 4. Then letters, numbers, or underscores.
        good_name = r'^[a-z]+_[a-z0-9_]+$'
        if not name or \
           not re.match(good_name, name):
            raise PLCInvalidArgument, "Invalid slice name"

        conflicts = Slices(self.api, [name])
        for slice_id, slice in conflicts.iteritems():
            if 'slice_id' not in self or self['slice_id'] != slice_id:
                raise PLCInvalidArgument, "Slice name already in use"

        return name

    def validate_instantiation(self, instantiation):
        instantiations = SliceInstantiations(self.api)
        if instantiation not in instantiations:
            raise PLCInvalidArgument, "No such instantiation state"

        return instantiation

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

    def add_person(self, person, commit = True):
        """
        Add person to existing slice.
        """

        assert 'slice_id' in self
        assert isinstance(person, PLC.Persons.Person)
        assert 'person_id' in person

        slice_id = self['slice_id']
        person_id = person['person_id']

        if person_id not in self['person_ids']:
            assert slice_id not in person['slice_ids']

            self.api.db.do("INSERT INTO slice_person (person_id, slice_id)" \
                           " VALUES(%(person_id)d, %(slice_id)d)",
                           locals())

            if commit:
                self.api.db.commit()

            self['person_ids'].append(person_id)
            person['slice_ids'].append(slice_id)

    def remove_person(self, person, commit = True):
        """
        Remove person from existing slice.
        """

        assert 'slice_id' in self
        assert isinstance(person, PLC.Persons.Person)
        assert 'person_id' in person

        slice_id = self['slice_id']
        person_id = person['person_id']

        if person_id in self['person_ids']:
            assert slice_id in person['slice_ids']

            self.api.db.do("DELETE FROM slice_person" \
                           " WHERE person_id = %(person_id)d" \
                           " AND slice_id = %(slice_id)d",
                           locals())

            if commit:
                self.api.db.commit()

            self['person_ids'].remove(person_id)
            person['slice_ids'].remove(slice_id)

    def add_node(self, node, commit = True):
        """
        Add node to existing slice.
        """

        assert 'slice_id' in self
        assert isinstance(node, Node)
        assert 'node_id' in node

        slice_id = self['slice_id']
        node_id = node['node_id']

        if node_id not in self['node_ids']:
            assert slice_id not in node['slice_ids']

            self.api.db.do("INSERT INTO slice_node (node_id, slice_id)" \
                           " VALUES(%(node_id)d, %(slice_id)d)",
                           locals())

            if commit:
                self.api.db.commit()

            self['node_ids'].append(node_id)
            node['slice_ids'].append(slice_id)

    def remove_node(self, node, commit = True):
        """
        Remove node from existing slice.
        """

        assert 'slice_id' in self
        assert isinstance(node, Node)
        assert 'node_id' in node

        slice_id = self['slice_id']
        node_id = node['node_id']

        if node_id in self['node_ids']:
            assert slice_id in node['slice_ids']

            self.api.db.do("DELETE FROM slice_node" \
                           " WHERE node_id = %(node_id)d" \
                           " AND slice_id = %(slice_id)d",
                           locals())

            if commit:
                self.api.db.commit()

            self['node_ids'].remove(node_id)
            node['slice_ids'].remove(slice_id)

    def sync(self, commit = True):
        """
        Add or update a slice.
        """

        # Before a new slice is added, delete expired slices
        if 'slice_id' not in self:
            expired = Slices(self.api, expires = -int(time.time())).values()
            for slice in expired:
                slice.delete(commit)

        Row.sync(self, commit)

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

    def __init__(self, api, slice_id_or_name_list = None, expires = int(time.time())):
        self.api = api

        sql = "SELECT %s FROM view_slices WHERE is_deleted IS False" % \
              ", ".join(Slice.fields)

        if expires is not None:
            if expires >= 0:
                sql += " AND expires > %(expires)d"
            else:
                expires = -expires
                sql += " AND expires < %(expires)d"

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

        rows = self.api.db.selectall(sql, locals())

        for row in rows:
            self[row['slice_id']] = slice = Slice(api, row)
            for aggregate in 'node_ids', 'person_ids', 'slice_attribute_ids':
                if not slice.has_key(aggregate) or slice[aggregate] is None:
                    slice[aggregate] = []
                else:
                    slice[aggregate] = map(int, slice[aggregate].split(','))
