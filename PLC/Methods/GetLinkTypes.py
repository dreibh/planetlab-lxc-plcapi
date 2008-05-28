#
# Thierry Parmentelat - INRIA
#
# $Revision: 9423 $
#
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.LinkTypes import LinkType, LinkTypes

class GetLinkTypes(Method):
    """
    Returns an array of structs containing details about
    ilink types.

    The usual filtering scheme applies on this method.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node']

    accepts = [
        Auth(),
        Mixed([Mixed(LinkType.fields['link_type_id'],
                     LinkType.fields['name'])],
              Filter(LinkType.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [LinkType.fields]

    def call(self, auth, link_type_filter = None, return_fields = None):
        return LinkTypes(self.api, link_type_filter, return_fields)
