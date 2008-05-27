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

class DeleteIlinkType(Method):
    """
    Deletes the specified ilink type.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Mixed(IlinkType.fields['ilink_type_id'],
              IlinkType.fields['name']),
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, ilink_type_id_or_name):
        ilink_types = IlinkTypes(self.api, [ilink_type_id_or_name])
        if not ilink_types:
            raise PLCInvalidArgument, "No such ilink type"
        ilink_type = ilink_types[0]

        ilink_type.delete()
	self.object_ids = [ilink_type['ilink_type_id']]

        return 1
