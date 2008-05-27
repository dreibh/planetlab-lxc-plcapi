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

class UpdateIlinkType(Method):
    """
    Updates the parameters of an existing tag type
    with the values in ilink_type_fields.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    ilink_type_fields = dict(filter(can_update, IlinkType.fields.items()))

    accepts = [
        Auth(),
        Mixed(IlinkType.fields['ilink_type_id'],
              IlinkType.fields['name']),
        ilink_type_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, ilink_type_id_or_name, ilink_type_fields):
        ilink_type_fields = dict(filter(can_update, ilink_type_fields.items()))

        ilink_types = IlinkTypes(self.api, [ilink_type_id_or_name])
        if not ilink_types:
            raise PLCInvalidArgument, "No such tag type"
        ilink_type = ilink_types[0]

        ilink_type.update(ilink_type_fields)
        ilink_type.sync()
	self.object_ids = [ilink_type['ilink_type_id']]

        return 1
