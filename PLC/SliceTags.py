#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Table import Row, Table
# seems to cause import loops
#from PLC.Slices import Slice, Slices
from PLC.Nodes import Node, Nodes
from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.TagTypes import TagType, TagTypes

class SliceTag(Row):
    """
    Representation of a row in the slice_tag table. To use,
    instantiate with a dict of values.
    """

    table_name = 'slice_tag'
    primary_key = 'slice_tag_id'
    fields = {
        'slice_tag_id': Parameter(int, "Slice tag identifier"),
        'slice_id': Parameter(int, "Slice identifier"),
        'name': Parameter(str, "Slice name"),
        'node_id': Node.fields['node_id'],
        'nodegroup_id': NodeGroup.fields['nodegroup_id'],
        'tag_type_id': TagType.fields['tag_type_id'],
        'tagname': TagType.fields['tagname'],
        'description': TagType.fields['description'],
        'category': TagType.fields['category'],
        'value': Parameter(str, "Slice attribute value"),
        }

class SliceTags(Table):
    """
    Representation of row(s) from the slice_tag table in the
    database.
    """

    def __init__(self, api, slice_tag_filter = None, columns = None):
        Table.__init__(self, api, SliceTag, columns)

        sql = "SELECT %s FROM view_slice_tags WHERE True" % \
              ", ".join(self.columns)

        if slice_tag_filter is not None:
            if isinstance(slice_tag_filter, (list, tuple, set, int, long)):
                slice_tag_filter = Filter(SliceTag.fields, {'slice_tag_id': slice_tag_filter})
            elif isinstance(slice_tag_filter, dict):
                slice_tag_filter = Filter(SliceTag.fields, slice_tag_filter)
            else:
                raise PLCInvalidArgument, "Wrong slice tag filter %r"%slice_tag_filter
            sql += " AND (%s) %s" % slice_tag_filter.sql(api)

        self.selectall(sql)
