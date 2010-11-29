#
# Thierry Parmentelat - INRIA
#

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.Sites import Sites
from PLC.Nodes import Node, Nodes
from PLC.TagTypes import TagType, TagTypes
from PLC.NodeTags import NodeTag, NodeTags

# need to import so the core classes get decorated with caller_may_write_tag
from PLC.AuthorizeHelpers import AuthorizeHelpers

class UpdateNodeTag(Method):
    """
    Updates the value of an existing node tag

    Admins have full access.  Non-admins need to 
    (1) have at least one of the roles attached to the tagtype, 
    and (2) belong in the same site as the tagged subject.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    accepts = [
        Auth(),
        NodeTag.fields['node_tag_id'],
        NodeTag.fields['value']
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, node_tag_id, value):
        node_tags = NodeTags(self.api, [node_tag_id])
        if not node_tags:
            raise PLCInvalidArgument, "No such node tag %r"%node_tag_id
        node_tag = node_tags[0]

        tag_type_id = node_tag['tag_type_id']
        tag_type = TagTypes (self.api,[tag_type_id])[0]

        nodes = Nodes (self.api, node_tag['node_id'])
        if not nodes:
            raise PLCInvalidArgument, "No such node %d"%node_tag['node_id']
        node=nodes[0]

        # check authorizations
        node.caller_may_write_tag(self.api,self.caller,tag_type)

        node_tag['value'] = value
        node_tag.sync()

        self.object_ids = [node_tag['node_tag_id']]
        return 1
