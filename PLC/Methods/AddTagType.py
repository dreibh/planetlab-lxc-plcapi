#
# Thierry Parmentelat - INRIA
#

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.TagTypes import TagType, TagTypes
from PLC.Auth import Auth

can_update = lambda (field, value): field in \
             ['tagname', 'description', 'category']

class AddTagType(Method):
    """
    Adds a new type of node tag.
    Any fields specified are used, otherwise defaults are used.

    Returns the new node_tag_id (> 0) if successful,
    faults otherwise.
    """

    roles = ['admin']

    tag_type_fields = dict(filter(can_update, TagType.fields.items()))

    accepts = [
        Auth(),
        tag_type_fields
        ]

    returns = Parameter(int, 'New node_tag_id (> 0) if successful')


    def call(self, auth, tag_type_fields):
        tag_type_fields = dict(filter(can_update, tag_type_fields.items()))
        tag_type = TagType(self.api, tag_type_fields)
        tag_type.sync()

        self.object_ids = [tag_type['tag_type_id']]

        return tag_type['tag_type_id']
