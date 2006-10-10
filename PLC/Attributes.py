from types import StringTypes

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Table import Row, Table
from PLC.Roles import Role, Roles

class Attribute(Row):
    """
    Representation of a row in the attributes table. To use, instantiate
    with a dict of values.
    """

    table_name = 'attributes'
    primary_key = 'attribute_id'
    fields = {
        'attribute_id': Parameter(int, "Attribute identifier"),
        'name': Parameter(str, "Attribute name", max = 100),
        'description': Parameter(str, "Attribute description", max = 254),
        'min_role_id': Parameter(int, "Minimum (least powerful) role that can set or change this attribute"),
        }

    def __init__(self, api, fields = {}):
        Row.__init__(self, fields)
        self.api = api

    def validate_name(self, name):
        name = name.strip()

        if not name:
            raise PLCInvalidArgument, "Attribute name must be set"

        conflicts = Attributes(self.api, [name])
        for attribute_id, attribute in conflicts.iteritems():
            if 'attribute_id' not in self or self['attribute_id'] != attribute_id:
                raise PLCInvalidArgument, "Attribute name already in use"

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

        assert 'attribute_id' in self

        # Clean up miscellaneous join tables
        for table in ['attributes', 'slice_attribute']:
            self.api.db.do("DELETE FROM %s" \
                           " WHERE attribute_id = %d" % \
                           (table, self['attribute_id']), self)

        if commit:
            self.api.db.commit()

class Attributes(Table):
    """
    Representation of row(s) from the attributes table in the
    database.
    """

    def __init__(self, api, attribute_id_or_name_list = None):
	self.api = api

        sql = "SELECT %s FROM attributes" % \
              ", ".join(Attribute.fields)

        if attribute_id_or_name_list:
            # Separate the list into integers and strings
            attribute_ids = filter(lambda attribute_id: isinstance(attribute_id, (int, long)),
                                   attribute_id_or_name_list)
            names = filter(lambda name: isinstance(name, StringTypes),
                           attribute_id_or_name_list)
            sql += " WHERE (False"
            if attribute_ids:
                sql += " OR attribute_id IN (%s)" % ", ".join(map(str, attribute_ids))
            if names:
                sql += " OR name IN (%s)" % ", ".join(api.db.quote(names))
            sql += ")"

        rows = self.api.db.selectall(sql)
 
        for row in rows:
            self[row['attribute_id']] = Attribute(api, row)
