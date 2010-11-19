#
# Thierry Parmentelat - INRIA
#
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.TagTypes import TagType, TagTypes

class GetTagTypes(Method):
    """
    Returns an array of structs containing details about
    node tag types.

    The usual filtering scheme applies on this method.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node']

    accepts = [
        Auth(),
        Mixed([Mixed(TagType.fields['tag_type_id'],
                     TagType.fields['tagname'])],
              Mixed(TagType.fields['tag_type_id'],
                     TagType.fields['tagname']),
              Filter(TagType.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [TagType.fields]

    def call(self, auth, tag_type_filter = None, return_fields = None):
        return TagTypes(self.api, tag_type_filter, return_fields)
