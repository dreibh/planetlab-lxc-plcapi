#
# Thierry Parmentelat - INRIA
#

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.Ilinks import Ilink, Ilinks
from PLC.Interfaces import Interface, Interfaces
from PLC.TagTypes import TagType, TagTypes
from PLC.Sites import Sites

from PLC.AuthorizeHelpers import AuthorizeHelpers

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

        src_if=Interfaces(self.api,ilink['src_interface_id'])[0]
        dst_if=Interfaces(self.api,ilink['dst_interface_id'])[0]
        tag_type_id = ilink['tag_type_id']
        tag_type = TagTypes (self.api,[tag_type_id])[0]

        # check authorizations
        if 'admin' in self.caller['roles']:
            pass
        elif not AuthorizeHelpers.caller_may_access_tag_type (self.api, self.caller, tag_type):
            raise PLCPermissionDenied, "%s, forbidden tag %s"%(self.name,tag_type['tagname'])
        elif AuthorizeHelpers.interface_belongs_to_person (self.api, src_if, self.caller):
            pass
        elif src_if_id != dst_if_id and AuthorizeHelpers.interface_belongs_to_person (self.api, dst_if, self.caller):
            pass
        else:
            raise PLCPermissionDenied, "%s: you must own either the src or dst interface"%self.name
            
        ilink['value'] = value
        ilink.sync()

        self.object_ids = [ilink['src_interface_id'],ilink['dst_interface_id']]
        return 1
