from types import StringTypes

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Table import Row, Table
from PLC.SliceAttributeTypes import SliceAttributeType, SliceAttributeTypes

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
        'attribute_type_id': SliceAttributeType.fields['attribute_type_id'],
        'name': SliceAttributeType.fields['name'],
        'description': SliceAttributeType.fields['description'],
        'min_role_id': SliceAttributeType.fields['min_role_id'],
        # XXX Arbitrary max, make configurable
        'value': Parameter(str, "Slice attribute value", max = 254),
        }

class SliceAttributes(Table):
    """
    Representation of row(s) from the slice_attribute table in the
    database.
    """

    def __init__(self, api, slice_attribute_id_list = None):
	self.api = api

        sql = "SELECT %s FROM view_slice_attributes" % \
              ", ".join(SliceAttribute.fields)

        if slice_attribute_id_list:
            sql += " WHERE slice_attribute_id IN (%s)" % ", ".join(map(str, slice_attribute_id_list))

        rows = self.api.db.selectall(sql)
 
        for row in rows:
            self[row['slice_attribute_id']] = SliceAttribute(api, row)
