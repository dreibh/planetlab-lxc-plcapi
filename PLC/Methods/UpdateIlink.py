# $Id$
# $URL$
#
# Thierry Parmentelat - INRIA
#
# $Revision: 9423 $
#

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.Ilinks import Ilink, Ilinks
from PLC.Interfaces import Interface, Interfaces

from PLC.Sites import Sites

class UpdateIlink(Method):
    """
    Updates the value of an existing ilink

    Access rights depend on the tag type.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    accepts = [
        Auth(),
        Ilink.fields['ilink_id'],
        Ilink.fields['value']
        ]

    returns = Parameter(int, '1 if successful')

    object_type = 'Interface'

    def call(self, auth, ilink_id, value):
        ilinks = Ilinks(self.api, [ilink_id])
        if not ilinks:
            raise PLCInvalidArgument, "No such ilink %r"%ilink_id
        ilink = ilinks[0]

        # xxx see AddIlink for this - should be written once in the Ilink class I guess
        # checks rights and stuff

        ilink['value'] = value
        ilink.sync()

	self.object_ids = [ilink['src_interface_id'],ilink['dst_interface_id']]
        return 1
