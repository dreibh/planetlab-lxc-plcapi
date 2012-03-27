from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.TagTypes import TagType, TagTypes
from PLC.NodeTags import NodeTag, NodeTags

can_update = lambda (field, value): field in NodeGroup.fields.keys() and field != NodeGroup.primary_field

class AddNodeGroup(Method):
    """
    Adds a new node group. Any values specified in nodegroup_fields
    are used, otherwise defaults are used.

    Returns the new nodegroup_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin']

    nodegroup_fields = dict(filter(can_update, NodeGroup.fields.items()))

    accepts = [
        Auth(),
        NodeGroup.fields['groupname'],
        Mixed(TagType.fields['tag_type_id'],
              TagType.fields['tagname']),
        NodeTag.fields['value'],
        ]

    returns = Parameter(int, 'New nodegroup_id (> 0) if successful')


    def call(self, auth, groupname, tag_type_id_or_tagname, value):
        # locate tag type
        tag_types = TagTypes (self.api,[tag_type_id_or_tagname])
        if not(tag_types):
            raise PLCInvalidArgument, "No such tag type %r"%tag_type_id_or_tagname
        tag_type=tag_types[0]

        nodegroup_fields = { 'groupname' : groupname,
                             'tag_type_id' : tag_type['tag_type_id'],
                             'value' : value }
        nodegroup = NodeGroup(self.api, nodegroup_fields)
        nodegroup.sync()

        # Logging variables
        self.event_objects = {'NodeGroup': [nodegroup['nodegroup_id']]}
        self.message = 'Node group %d created' % nodegroup['nodegroup_id']

        return nodegroup['nodegroup_id']
