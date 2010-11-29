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

# need to import so the core classes get decorated with caller_may_write_tag
from PLC.AuthorizeHelpers import AuthorizeHelpers

class DeleteInterfaceTag(Method):
    """
    Deletes the specified interface setting

    Admins have full access.  Non-admins need to 
    (1) have at least one of the roles attached to the tagtype, 
    and (2) belong in the same site as the tagged subject.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        Auth(),
        InterfaceTag.fields['interface_tag_id']
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, interface_tag_id):
        interface_tags = InterfaceTags(self.api, [interface_tag_id])
        if not interface_tags:
            raise PLCInvalidArgument, "No such interface tag %r"%interface_tag_id
        interface_tag = interface_tags[0]

        tag_type_id = interface_tag['tag_type_id']
        tag_type = TagTypes (self.api,[tag_type_id])[0]

        interfaces = Interfaces (self.api, interface_tag['interface_id'])
        if not interfaces:
            raise PLCInvalidArgument, "No such interface %d"%interface_tag['interface_id']
        interface=interfaces[0]

        # check authorizations
        interface.caller_may_write_tag(self.api,self.caller,tag_type)

        interface_tag.delete()
        self.object_ids = [interface_tag['interface_tag_id']]

        return 1
