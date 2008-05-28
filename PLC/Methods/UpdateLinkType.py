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

can_update = lambda (field, value): field in \
             ['name', 'description', 'category', 'min_role_id']

class UpdateLinkType(Method):
    """
    Updates the parameters of an existing link type
    with the values in link_type_fields.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    link_type_fields = dict(filter(can_update, LinkType.fields.items()))

    accepts = [
        Auth(),
        Mixed(LinkType.fields['link_type_id'],
              LinkType.fields['name']),
        link_type_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, link_type_id_or_name, link_type_fields):
        link_type_fields = dict(filter(can_update, link_type_fields.items()))

        link_types = LinkTypes(self.api, [link_type_id_or_name])
        if not link_types:
            raise PLCInvalidArgument, "No such tag type"
        link_type = link_types[0]

        link_type.update(link_type_fields)
        link_type.sync()
	self.object_ids = [link_type['link_type_id']]

        return 1
