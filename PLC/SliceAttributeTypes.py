from types import StringTypes

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Table import Row, Table
from PLC.Roles import Role, Roles

class SliceAttributeType(Row):
    """
    Representation of a row in the slice_attribute_types table. To
    use, instantiate with a dict of values.
    """

    table_name = 'slice_attribute_types'
    primary_key = 'attribute_type_id'
    fields = {
        'attribute_type_id': Parameter(int, "Slice attribute type identifier"),
        'name': Parameter(str, "Slice attribute type name", max = 100),
        'description': Parameter(str, "Slice attribute type description", max = 254),
        'min_role_id': Parameter(int, "Minimum (least powerful) role that can set or change this attribute"),
        }

    def __init__(self, api, fields = {}):
        Row.__init__(self, fields)
        self.api = api

    def validate_name(self, name):
        name = name.strip()

        if not name:
            raise PLCInvalidArgument, "Slice attribute type name must be set"

        conflicts = SliceAttributeTypes(self.api, [name])
        for attribute_type_id, attribute in conflicts.iteritems():
            if 'attribute_type_id' not in self or self['attribute_type_id'] != attribute_type_id:
                raise PLCInvalidArgument, "Slice attribute type name already in use"

        return name

    def validate_min_role_id(self, role_id):
        roles = Roles(self.api)
        if role_id not in roles:
            raise PLCInvalidArgument, "Invalid role"

        return role_id

    def delete(self, commit = True):
        """
        Delete existing slice attribute type.
        """

        assert 'attribute_type_id' in self

        # Clean up miscellaneous join tables
        for table in ['slice_attribute_types', 'slice_attribute']:
            self.api.db.do("DELETE FROM %s" \
                           " WHERE attribute_type_id = %d" % \
                           (table, self['attribute_type_id']), self)

        if commit:
            self.api.db.commit()

class SliceAttributeTypes(Table):
    """
    Representation of row(s) from the slice_attribute_types table in the
    database.
    """

    def __init__(self, api, attribute_type_id_or_name_list = None):
	self.api = api

        sql = "SELECT %s FROM slice_attribute_types" % \
              ", ".join(SliceAttributeType.fields)

        if attribute_type_id_or_name_list:
            # Separate the list into integers and strings
            attribute_type_ids = filter(lambda attribute_type_id: isinstance(attribute_type_id, (int, long)),
                                   attribute_type_id_or_name_list)
            names = filter(lambda name: isinstance(name, StringTypes),
                           attribute_type_id_or_name_list)
            sql += " WHERE (False"
            if attribute_type_ids:
                sql += " OR attribute_type_id IN (%s)" % ", ".join(map(str, attribute_type_ids))
            if names:
                sql += " OR name IN (%s)" % ", ".join(api.db.quote(names))
            sql += ")"

        rows = self.api.db.selectall(sql)
 
        for row in rows:
            self[row['attribute_type_id']] = SliceAttributeType(api, row)
