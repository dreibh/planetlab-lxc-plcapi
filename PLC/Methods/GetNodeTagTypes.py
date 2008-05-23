#
# Thierry Parmentelat - INRIA
#
# $Revision: 9423 $
#
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.NodeTagTypes import NodeTagType, NodeTagTypes

class GetNodeTagTypes(Method):
    """
    Returns an array of structs containing details about
    node tag types.

    The usual filtering scheme applies on this method.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node']

    accepts = [
        Auth(),
        Mixed([Mixed(NodeTagType.fields['node_tag_type_id'],
                     NodeTagType.fields['tagname'])],
              Filter(NodeTagType.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [NodeTagType.fields]

    def call(self, auth, node_tag_type_filter = None, return_fields = None):
        return NodeTagTypes(self.api, node_tag_type_filter, return_fields)
