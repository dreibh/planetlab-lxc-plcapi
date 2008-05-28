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

class AddLinkType(Method):
    """
    Adds a new type of ilink.
    Any fields specified are used, otherwise defaults are used.

    Returns the new ilink_id (> 0) if successful,
    faults otherwise.
    """

    roles = ['admin']

    link_type_fields = dict(filter(can_update, LinkType.fields.items()))

    accepts = [
        Auth(),
        link_type_fields
        ]

    returns = Parameter(int, 'New ilink_id (> 0) if successful')


    def call(self, auth, link_type_fields):
        link_type_fields = dict(filter(can_update, link_type_fields.items()))
        link_type = LinkType(self.api, link_type_fields)
        link_type.sync()

	self.object_ids = [link_type['link_type_id']]

        return link_type['link_type_id']
