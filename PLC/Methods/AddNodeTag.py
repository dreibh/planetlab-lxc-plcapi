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

from PLC.AuthorizeHelpers import AuthorizeHelpers

class AddNodeTag(Method):
    """
    Sets the specified tag for the specified node
    to the specified value.

    Admins have full access.  Non-admins need to 
    (1) have at least one of the roles attached to the tagtype, 
    and (2) belong in the same site as the tagged subject.

    Returns the new node_tag_id (> 0) if successful, faults
    otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    accepts = [
        Auth(),
        # no other way to refer to a node
        Mixed(Node.fields['node_id'],
              Node.fields['hostname']),
        Mixed(TagType.fields['tag_type_id'],
              TagType.fields['tagname']),
        NodeTag.fields['value'],
        ]

    returns = Parameter(int, 'New node_tag_id (> 0) if successful')

    def call(self, auth, node_id, tag_type_id_or_name, value):
        nodes = Nodes(self.api, [node_id])
        if not nodes:
            raise PLCInvalidArgument, "No such node %r"%node_id
        node = nodes[0]

        tag_types = TagTypes(self.api, [tag_type_id_or_name])
        if not tag_types:
            raise PLCInvalidArgument, "No such node tag type %r"%tag_type_id_or_name
        tag_type = tag_types[0]

        # checks for existence - does not allow several different tags
        conflicts = NodeTags(self.api,
                                        {'node_id':node['node_id'],
                                         'tag_type_id':tag_type['tag_type_id']})

        if len(conflicts) :
            raise PLCInvalidArgument, "Node %d already has tag %d"%(node['node_id'],
                                                                    tag_type['tag_type_id'])


        # check authorizations
        if 'admin' in self.caller['roles']:
            pass
        elif not AuthorizeHelpers.person_access_tag_type (self.api, self.caller, tag_type):
            raise PLCPermissionDenied, "%s, no permission to use this tag type"%self.name
        elif AuthorizeHelpers.node_belongs_to_person (self.api, node, self.caller):
            pass
        else:
            raise PLCPermissionDenied, "%s: you must belong in the same site as subject node"%self.name


        node_tag = NodeTag(self.api)
        node_tag['node_id'] = node['node_id']
        node_tag['tag_type_id'] = tag_type['tag_type_id']
        node_tag['value'] = value

        node_tag.sync()
        self.object_ids = [node_tag['node_tag_id']]

        return node_tag['node_tag_id']
