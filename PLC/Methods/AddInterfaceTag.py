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

class AddInterfaceTag(Method):
    """
    Sets the specified setting for the specified interface
    to the specified value.

    Admins have full access.  Non-admins need to 
    (1) have at least one of the roles attached to the tagtype, 
    and (2) belong in the same site as the tagged subject.

    Returns the new interface_tag_id (> 0) if successful, faults
    otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    accepts = [
        Auth(),
        # no other way to refer to a interface
        InterfaceTag.fields['interface_id'],
        Mixed(TagType.fields['tag_type_id'],
              TagType.fields['tagname']),
        InterfaceTag.fields['value'],
        ]

    returns = Parameter(int, 'New interface_tag_id (> 0) if successful')

    def call(self, auth, interface_id, tag_type_id_or_name, value):
        interfaces = Interfaces(self.api, [interface_id])
        if not interfaces:
            raise PLCInvalidArgument, "No such interface %r"%interface_id
        interface = interfaces[0]

        tag_types = TagTypes(self.api, [tag_type_id_or_name])
        if not tag_types:
            raise PLCInvalidArgument, "No such tag type %r"%tag_type_id_or_name
        tag_type = tag_types[0]

        # checks for existence - does not allow several different settings
        conflicts = InterfaceTags(self.api,
                                        {'interface_id':interface['interface_id'],
                                         'tag_type_id':tag_type['tag_type_id']})

        if len(conflicts) :
            raise PLCInvalidArgument, "Interface %d already has setting %d"%(interface['interface_id'],
                                                                               tag_type['tag_type_id'])

        # check authorizations
        interface.caller_may_write_tag(self.api,self.caller,tag_type)

        interface_tag = InterfaceTag(self.api)
        interface_tag['interface_id'] = interface['interface_id']
        interface_tag['tag_type_id'] = tag_type['tag_type_id']
        interface_tag['value'] = value

        interface_tag.sync()
        self.object_ids = [interface_tag['interface_tag_id']]

        return interface_tag['interface_tag_id']
