#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.TagTypes import TagType, TagTypes
from PLC.Auth import Auth

class DeleteTagType(Method):
    """
    Deletes the specified node tag type.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Mixed(TagType.fields['tag_type_id'],
              TagType.fields['tagname']),
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, tag_type_id_or_name):
        tag_types = TagTypes(self.api, [tag_type_id_or_name])
        if not tag_types:
            raise PLCInvalidArgument, "No such node tag type"
        tag_type = tag_types[0]

        tag_type.delete()
        self.object_ids = [tag_type['tag_type_id']]

        return 1
