#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.TagTypes import TagType, TagTypes
from PLC.Ilinks import Ilink, Ilinks
from PLC.Interfaces import Interface, Interfaces
from PLC.Sites import Sites

from PLC.AuthorizeHelpers import AuthorizeHelpers

class AddIlink(Method):
    """
    Create a link between two interfaces
    The link has a tag type, that needs be created beforehand
    and an optional value.

    Returns the new ilink_id (> 0) if successful, faults
    otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    accepts = [
        Auth(),
        # refer to either the id or the type name
        Ilink.fields['src_interface_id'],
        Ilink.fields['dst_interface_id'],
        Mixed(TagType.fields['tag_type_id'],
              TagType.fields['tagname']),
        Ilink.fields['value'],
        ]

    returns = Parameter(int, 'New ilink_id (> 0) if successful')

    def call(self, auth,  src_if_id, dst_if_id, tag_type_id_or_name, value):

        src_if = Interfaces (self.api, [src_if_id],['interface_id'])
        if not src_if:
            raise PLCInvalidArgument, "No such source interface %r"%src_if_id
        dst_if = Interfaces (self.api, [dst_if_id],['interface_id'])
        if not dst_if:
            raise PLCInvalidArgument, "No such destination interface %r"%dst_if_id

        tag_types = TagTypes(self.api, [tag_type_id_or_name])
        if not tag_types:
            raise PLCInvalidArgument, "AddIlink: No such tag type %r"%tag_type_id_or_name
        tag_type = tag_types[0]

        # checks for existence - with the same type
        conflicts = Ilinks(self.api,
                           {'tag_type_id':tag_type['tag_type_id'],
                            'src_interface_id':src_if_id,
                            'dst_interface_id':dst_if_id,})

        if len(conflicts) :
            ilink=conflicts[0]
            raise PLCInvalidArgument, "Ilink (%s,%d,%d) already exists and has value %r"\
                %(tag_type['name'],src_if_id,dst_if_id,ilink['value'])

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
            raise PLCPermissionDenied, "%s: you must one either the src or dst interface"%self.name
            
        ilink = Ilink(self.api)
        ilink['tag_type_id'] = tag_type['tag_type_id']
        ilink['src_interface_id'] = src_if_id
        ilink['dst_interface_id'] = dst_if_id
        ilink['value'] = value

        ilink.sync()

        self.object_type = 'Interface'
        self.object_ids = [src_if_id,dst_if_id]

        return ilink['ilink_id']
