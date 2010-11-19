#
# Thierry Parmentelat - INRIA
#

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.Sites import Site, Sites
from PLC.Nodes import Node, Nodes
from PLC.TagTypes import TagType, TagTypes
from PLC.NodeTags import NodeTag, NodeTags

from PLC.AuthorizeHelpers import AuthorizeHelpers

class DeleteNodeTag(Method):
    """
    Deletes the specified node tag

    Admins have full access.  Non-admins need to 
    (1) have at least one of the roles attached to the tagtype, 
    and (2) belong in the same site as the tagged subject.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        Auth(),
        NodeTag.fields['node_tag_id']
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, node_tag_id):
        node_tags = NodeTags(self.api, [node_tag_id])
        if not node_tags:
            raise PLCInvalidArgument, "No such node tag %r"%node_tag_id
        node_tag = node_tags[0]

        tag_type_id = node_tag['tag_type_id']
        tag_type = TagTypes (self.api,[tag_type_id])[0]
        node = Nodes (self.api, node_tag['node_id'])

        # check authorizations
        if 'admin' in self.caller['roles']:
            pass
        elif not AuthorizeHelpers.caller_may_access_tag_type (self.api, self.caller, tag_type):
            raise PLCPermissionDenied, "%s, forbidden tag %s"%(self.name,tag_type['tagname'])
        elif AuthorizeHelpers.node_belongs_to_person (self.api, node, self.caller):
            pass
        else:
            raise PLCPermissionDenied, "%s: you must belong in the same site as subject node"%self.name

        node_tag.delete()
        self.object_ids = [node_tag['node_tag_id']]

        return 1
