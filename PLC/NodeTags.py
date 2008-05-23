#
# Thierry Parmentelat - INRIA
#
# $Revision: 9423 $
#
from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Table import Row, Table
from PLC.NodeTagTypes import NodeTagType, NodeTagTypes

class NodeTag(Row):
    """
    Representation of a row in the node_tag.
    To use, instantiate with a dict of values.
    """

    table_name = 'node_tag'
    primary_key = 'node_tag_id'
    fields = {
        'node_tag_id': Parameter(int, "Node tag identifier"),
        'node_id': Parameter(int, "Node identifier"),
        'node_tag_type_id': NodeTagType.fields['node_tag_type_id'],
        'name': NodeTagType.fields['name'],
        'description': NodeTagType.fields['description'],
        'category': NodeTagType.fields['category'],
        'min_role_id': NodeTagType.fields['min_role_id'],
        'value': Parameter(str, "Node tag value"),
	### relations
	
        }

class NodeTags(Table):
    """
    Representation of row(s) from the node_tag table in the
    database.
    """

    def __init__(self, api, node_tag_filter = None, columns = None):
        Table.__init__(self, api, NodeTag, columns)

        sql = "SELECT %s FROM view_node_tags WHERE True" % \
              ", ".join(self.columns)

        if node_tag_filter is not None:
            if isinstance(node_tag_filter, (list, tuple, set)):
                node_tag_filter = Filter(NodeTag.fields, {'node_tag_id': node_tag_filter})
            elif isinstance(node_tag_filter, dict):
                node_tag_filter = Filter(NodeTag.fields, node_tag_filter)
            elif isinstance(node_tag_filter, int):
                node_tag_filter = Filter(NodeTag.fields, {'node_tag_id': [node_tag_filter]})
            else:
                raise PLCInvalidArgument, "Wrong node tag filter %r"%node_tag_filter
            sql += " AND (%s) %s" % node_tag_filter.sql(api)


        self.selectall(sql)
