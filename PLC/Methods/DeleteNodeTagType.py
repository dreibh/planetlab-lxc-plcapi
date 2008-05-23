#
# Thierry Parmentelat - INRIA
#
# $Revision: 9423 $
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NodeTagTypes import NodeTagType, NodeTagTypes
from PLC.Auth import Auth

class DeleteNodeTagType(Method):
    """
    Deletes the specified node tag type.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Mixed(NodeTagType.fields['node_tag_type_id'],
              NodeTagType.fields['tagname']),
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, node_tag_type_id_or_name):
        node_tag_types = NodeTagTypes(self.api, [node_tag_type_id_or_name])
        if not node_tag_types:
            raise PLCInvalidArgument, "No such node tag type"
        node_tag_type = node_tag_types[0]

        node_tag_type.delete()
	self.object_ids = [node_tag_type['node_tag_type_id']]

        return 1
