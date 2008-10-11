# $Id#
from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Table import Row, Table
from PLC.TagTypes import TagType, TagTypes

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
	'nodegroup_id': Parameter(int, "Nodegroup identifier, if a sliver attribute"),
        'tag_type_id': TagType.fields['tag_type_id'],
        'tagname': TagType.fields['tagname'],
        'description': TagType.fields['description'],
        'category': TagType.fields['category'],
        'min_role_id': TagType.fields['min_role_id'],
        'value': Parameter(str, "Slice attribute value"),
        }

class SliceAttributes(Table):
    """
    Representation of row(s) from the slice_attribute table in the
    database.
    """

    def __init__(self, api, slice_attribute_filter = None, columns = None):
        Table.__init__(self, api, SliceAttribute, columns)

        sql = "SELECT %s FROM view_slice_attributes WHERE True" % \
              ", ".join(self.columns)

        if slice_attribute_filter is not None:
            if isinstance(slice_attribute_filter, (list, tuple, set)):
                slice_attribute_filter = Filter(SliceAttribute.fields, {'slice_attribute_id': slice_attribute_filter})
            elif isinstance(slice_attribute_filter, dict):
                slice_attribute_filter = Filter(SliceAttribute.fields, slice_attribute_filter)
            sql += " AND (%s) %s" % slice_attribute_filter.sql(api)

        self.selectall(sql)
