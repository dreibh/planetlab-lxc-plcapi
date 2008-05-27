#
# Thierry Parmentelat - INRIA
#
# $Revision: 9423 $
#
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.IlinkTypes import IlinkType, IlinkTypes

class GetIlinkTypes(Method):
    """
    Returns an array of structs containing details about
    ilink types.

    The usual filtering scheme applies on this method.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node']

    accepts = [
        Auth(),
        Mixed([Mixed(IlinkType.fields['ilink_type_id'],
                     IlinkType.fields['name'])],
              Filter(IlinkType.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [IlinkType.fields]

    def call(self, auth, ilink_type_filter = None, return_fields = None):
        return IlinkTypes(self.api, ilink_type_filter, return_fields)
