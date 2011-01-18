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

class UpdateTagType(Method):
    """
    Updates the parameters of an existing tag type
    with the values in tag_type_fields.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    tag_type_fields = dict(filter(can_update, TagType.fields.items()))

    accepts = [
        Auth(),
        Mixed(TagType.fields['tag_type_id'],
              TagType.fields['tagname']),
        tag_type_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, tag_type_id_or_name, tag_type_fields):
        
        accepted_type_fields = dict(filter(can_update, tag_type_fields.items()))
        rejected_keys = [ k for k in tag_type_fields if k not in accepted_type_fields ]
        if rejected_keys:
            error="Cannot update TagType column(s) %r"%rejected_keys
            if 'roles' in rejected_keys or 'role_ids' in rejected_keys:
                error += " see AddRoleToTagType DeleteRoleFromTagType"
            raise PLCInvalidArgument, error

        tag_types = TagTypes(self.api, [tag_type_id_or_name])
        if not tag_types:
            raise PLCInvalidArgument, "No such tag type"
        tag_type = tag_types[0]

        tag_type.update(accepted_type_fields)
        tag_type.sync()
        self.object_ids = [tag_type['tag_type_id']]

        return 1
