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

can_update = lambda (field, value): field in \
             ['name', 'description', 'category', 'min_role_id']

class UpdateNodeTagType(Method):
    """
    Updates the parameters of an existing tag type
    with the values in node_tag_type_fields.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    node_tag_type_fields = dict(filter(can_update, NodeTagType.fields.items()))

    accepts = [
        Auth(),
        Mixed(NodeTagType.fields['node_tag_type_id'],
              NodeTagType.fields['name']),
        node_tag_type_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, node_tag_type_id_or_name, node_tag_type_fields):
        node_tag_type_fields = dict(filter(can_update, node_tag_type_fields.items()))

        node_tag_types = NodeTagTypes(self.api, [node_tag_type_id_or_name])
        if not node_tag_types:
            raise PLCInvalidArgument, "No such tag type"
        node_tag_type = node_tag_types[0]

        node_tag_type.update(node_tag_type_fields)
        node_tag_type.sync()
	self.object_ids = [node_tag_type['node_tag_type_id']]

        return 1
