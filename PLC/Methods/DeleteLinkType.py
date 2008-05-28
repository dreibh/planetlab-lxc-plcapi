#
# Thierry Parmentelat - INRIA
#
# $Revision: 9423 $
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.LinkTypes import LinkType, LinkTypes
from PLC.Auth import Auth

class DeleteLinkType(Method):
    """
    Deletes the specified ilink type.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Mixed(LinkType.fields['link_type_id'],
              LinkType.fields['name']),
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, link_type_id_or_name):
        link_types = LinkTypes(self.api, [link_type_id_or_name])
        if not link_types:
            raise PLCInvalidArgument, "No such ilink type"
        link_type = link_types[0]

        link_type.delete()
	self.object_ids = [link_type['link_type_id']]

        return 1
