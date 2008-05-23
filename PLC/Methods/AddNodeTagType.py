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

class AddNodeTagType(Method):
    """
    Adds a new type of node tag.
    Any fields specified are used, otherwise defaults are used.

    Returns the new node_tag_id (> 0) if successful,
    faults otherwise.
    """

    roles = ['admin']

    node_tag_type_fields = dict(filter(can_update, NodeTagType.fields.items()))

    accepts = [
        Auth(),
        node_tag_type_fields
        ]

    returns = Parameter(int, 'New node_tag_id (> 0) if successful')


    def call(self, auth, node_tag_type_fields):
        node_tag_type_fields = dict(filter(can_update, node_tag_type_fields.items()))
        node_tag_type = NodeTagType(self.api, node_tag_type_fields)
        node_tag_type.sync()

	self.object_ids = [node_tag_type['node_tag_type_id']]

        return node_tag_type['node_tag_type_id']
