from types import StringTypes

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Table import Row, Table
from PLC.Attributes import Attribute, Attributes

class SliceAttribute(Row):
    """
    Representation of a row in the slice_attribute table. To use,
    instantiate with a dict of values.
    """

    table_name = 'slice_attribute'
    primary_key = 'slice_attribute_id'
    fields = {
        'slice_attribute_id': Parameter(int, "Slice attribute identifier"),
        'slice_id': Parameter(int, "Slice identifier"),
        'node_id': Parameter(int, "Node identifier, if a sliver attribute"),
        'attribute_id': Attribute.fields['attribute_id'],
        'name': Attribute.fields['name'],
        'description': Attribute.fields['description'],
        'min_role_id': Attribute.fields['min_role_id'],
        # XXX Arbitrary max, make configurable
        'value': Parameter(str, "Slice attribute value", max = 254),
        }

    def __init__(self, api, fields = {}):
        Row.__init__(self, fields)
        self.api = api

    def delete(self, commit = True):
        """
        Delete existing slice attribute.
        """

        assert 'slice_attribute_id' in self

        # Clean up miscellaneous join tables
        for table in 'slice_attribute',:
            self.api.db.do("DELETE FROM %s" \
                           " WHERE slice_attribute_id = %d" % \
                           (table, self['slice_attribute_id']), self)

        if commit:
            self.api.db.commit()

class SliceAttributes(dict):
    """
    Representation of row(s) from the slice_attribute table in the
    database.
    """

    def __init__(self, api, slice_attribute_id_list):
	self.api = api

        sql = "SELECT %s FROM view_slice_attributes" % \
              ", ".join(SliceAttribute.fields)

        sql += " WHERE slice_attribute_id IN (%s)" % ", ".join(map(str, slice_attribute_id_list))

        rows = self.api.db.selectall(sql)
 
        for row in rows:
            self[row['slice_attribute_id']] = SliceAttribute(api, row)
