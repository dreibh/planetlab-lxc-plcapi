#
# Thierry Parmentelat - INRIA
#

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.Ilinks import Ilink, Ilinks
from PLC.Interfaces import Interface, Interfaces
from PLC.Nodes import Node, Nodes
from PLC.Sites import Site, Sites
from PLC.TagTypes import TagType, TagTypes

from PLC.AuthorizeHelpers import AuthorizeHelpers

class DeleteIlink(Method):
    """
    Deletes the specified ilink

    Attributes may require the caller to have a particular
    role in order to be deleted, depending on the related tag type.
    Admins may delete attributes of any slice or sliver.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        Ilink.fields['ilink_id']
        ]

    returns = Parameter(int, '1 if successful')

    object_type = 'Interface'


    def call(self, auth, ilink_id):
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
            
        ilink.delete()
        self.object_ids = [ilink['src_interface_id'],ilink['dst_interface_id']]

        return 1
