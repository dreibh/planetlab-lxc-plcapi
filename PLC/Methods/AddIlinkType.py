#
# Thierry Parmentelat - INRIA
#
# $Revision: 9423 $
#


from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.IlinkTypes import IlinkType, IlinkTypes
from PLC.Auth import Auth

can_update = lambda (field, value): field in \
             ['name', 'description', 'category', 'min_role_id']

class AddIlinkType(Method):
    """
    Adds a new type of ilink.
    Any fields specified are used, otherwise defaults are used.

    Returns the new ilink_id (> 0) if successful,
    faults otherwise.
    """

    roles = ['admin']

    ilink_type_fields = dict(filter(can_update, IlinkType.fields.items()))

    accepts = [
        Auth(),
        ilink_type_fields
        ]

    returns = Parameter(int, 'New ilink_id (> 0) if successful')


    def call(self, auth, ilink_type_fields):
        ilink_type_fields = dict(filter(can_update, ilink_type_fields.items()))
        ilink_type = IlinkType(self.api, ilink_type_fields)
        ilink_type.sync()

	self.object_ids = [ilink_type['ilink_type_id']]

        return ilink_type['ilink_type_id']
