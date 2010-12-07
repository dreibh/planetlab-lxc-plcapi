#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth

from PLC.NodeTags import NodeTag, NodeTags
from PLC.Sites import Site, Sites
from PLC.Nodes import Node, Nodes

class GetNodeTags(Method):
    """
    Returns an array of structs containing details about
    nodes and related tags.

    If node_tag_filter is specified and is an array of
    node tag identifiers, only node tags matching
    the filter will be returned. If return_fields is specified, only
    the specified details will be returned.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node']

    accepts = [
        Auth(),
        Mixed([NodeTag.fields['node_tag_id']],
              Parameter(int,"Node tag id"),
              Filter(NodeTag.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [NodeTag.fields]


    def call(self, auth, node_tag_filter = None, return_fields = None):

        node_tags = NodeTags(self.api, node_tag_filter, return_fields)

        return node_tags
