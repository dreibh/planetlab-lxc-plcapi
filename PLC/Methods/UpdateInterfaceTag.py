#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.Sites import Sites
from PLC.Nodes import Nodes
from PLC.Interfaces import Interface, Interfaces
from PLC.TagTypes import TagType, TagTypes
from PLC.InterfaceTags import InterfaceTag, InterfaceTags

class UpdateInterfaceTag(Method):
    """
    Updates the value of an existing interface setting

    Admins have full access.  Non-admins need to 
    (1) have at least one of the roles attached to the tagtype, 
    and (2) belong in the same site as the tagged subject.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    accepts = [
        Auth(),
        InterfaceTag.fields['interface_tag_id'],
        InterfaceTag.fields['value']
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, interface_tag_id, value):
        interface_tags = InterfaceTags(self.api, [interface_tag_id])
        if not interface_tags:
            raise PLCInvalidArgument, "No such interface setting %r"%interface_tag_id
        interface_tag = interface_tags[0]

        tag_type_id = interface_tag['tag_type_id']
        tag_type = TagTypes (self.api,[tag_type_id])[0]

        interfaces = Interfaces (self.api, interface_tag['interface_id'])
        if not interfaces:
            raise PLCInvalidArgument, "No such interface %d"%interface_tag['interface_id']
        interface=interfaces[0]

        # check authorizations
        if 'admin' in self.caller['roles']:
            pass
        elif not AuthorizeHelpers.caller_may_access_tag_type (self.api, self.caller, tag_type):
            raise PLCPermissionDenied, "%s, forbidden tag %s"%(self.name,tag_type['tagname'])
        elif AuthorizeHelpers.interface_belongs_to_person (self.api, interface, self.caller):
            pass
        else:
            raise PLCPermissionDenied, "%s: you must belong in the same site as subject interface"%self.name


        interface_tag['value'] = value
        interface_tag.sync()

        self.object_ids = [interface_tag['interface_tag_id']]
        return 1
