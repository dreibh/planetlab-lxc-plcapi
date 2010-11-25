#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.TagTypes import TagType, TagTypes
from PLC.Slices import Slice, Slices
from PLC.Nodes import Node, Nodes
from PLC.SliceTags import SliceTag, SliceTags
from PLC.NodeGroups import NodeGroup, NodeGroups
from PLC.InitScripts import InitScript, InitScripts

class AddSliceTag(Method):
    """
    Sets the specified tag of the slice to the specified value.
    If nodegroup is specified, this applies to all slivers of that group.
    If node is specified, this only applies to a sliver.

    Admins have full access, including on nodegroups.

    Non-admins need to have at least one of the roles 
    attached to the tagtype. In addition:
    (*) Users may only set tags of slices or slivers of which they are members. 
    (*) PIs may only set tags of slices in their site
    (*) techs cannot use this method

    Returns the new slice_tag_id (> 0) if successful, faults
    otherwise.
    """

    roles = ['admin', 'pi', 'user', 'node']

    accepts = [
        Auth(),
        Mixed(Slice.fields['slice_id'],
              Slice.fields['name']),
        Mixed(SliceTag.fields['tag_type_id'],
              SliceTag.fields['tagname']),
        Mixed(SliceTag.fields['value'],
              InitScript.fields['name']),
        Mixed(Node.fields['node_id'],
              Node.fields['hostname'],
              None),
        Mixed(NodeGroup.fields['nodegroup_id'],
              NodeGroup.fields['groupname'])
        ]

    returns = Parameter(int, 'New slice_tag_id (> 0) if successful')

    def call(self, auth, slice_id_or_name, tag_type_id_or_name, value, node_id_or_hostname = None, nodegroup_id_or_name = None):
        slices = Slices(self.api, [slice_id_or_name])
        if not slices:
            raise PLCInvalidArgument, "No such slice %r"%slice_id_or_name
        slice = slices[0]

        tag_types = TagTypes(self.api, [tag_type_id_or_name])
        if not tag_types:
            raise PLCInvalidArgument, "No such tag type %r"%tag_type_id_or_name
        tag_type = tag_types[0]

        # check authorizations
        slice.caller_may_write_tag (self.api,self.caller,tag_type,node_id_or_hostname,nodegroup_id_or_name)

        # if initscript is specified, validate value
        if tag_type['tagname'] in ['initscript']:
            initscripts = InitScripts(self.api, {'enabled': True, 'name': value})
            if not initscripts:
                raise PLCInvalidArgument, "No such plc initscript %r"%value

        slice_tag = SliceTag(self.api)
        slice_tag['slice_id'] = slice['slice_id']
        slice_tag['tag_type_id'] = tag_type['tag_type_id']
        slice_tag['value'] = unicode(value)

        # Sliver attribute if node is specified
        if node_id_or_hostname is not None or isinstance(self.caller, Node):
            node_id = None
            if isinstance(self.caller, Node):
                node = self.caller
                node_id = node['node_id']

            if node_id_or_hostname is not None:
                nodes = Nodes(self.api, [node_id_or_hostname])
                if not nodes:
                    raise PLCInvalidArgument, "No such node"
                node = nodes[0]
                if node_id <> None and node_id <> node['node_id']:
                    raise PLCPermissionDenied, "Not allowed to set another node's sliver attribute"
                else:
                    node_id = node['node_id']

            system_slice_tags = SliceTags(self.api, {'tagname': 'system', 'value': '1'}).dict('slice_id')
            system_slice_ids = system_slice_tags.keys()
            if slice['slice_id'] not in system_slice_ids and node_id not in slice['node_ids']:
                raise PLCInvalidArgument, "AddSliceTag: slice %s not on specified node %s nor is it a system slice (%r)"%\
                    (slice['name'],node['hostname'],system_slice_ids)
            slice_tag['node_id'] = node['node_id']

        # Sliver attribute shared accross nodes if nodegroup is sepcified
        if nodegroup_id_or_name is not None:
            if isinstance(self.caller, Node):
                raise PLCPermissionDenied, "Not allowed to set nodegroup slice attributes"

            nodegroups = NodeGroups(self.api, [nodegroup_id_or_name])
            if not nodegroups:
                raise PLCInvalidArgument, "No such nodegroup %r"%nodegroup_id_or_name
            nodegroup = nodegroups[0]

            slice_tag['nodegroup_id'] = nodegroup['nodegroup_id']

        # Check if slice attribute already exists
        slice_tags_check = SliceTags(self.api, {'slice_id': slice['slice_id'],
                                                'tagname': tag_type['tagname'],
                                                'value': value})
        for slice_tag_check in slice_tags_check:
            # do not compare between slice tag and sliver tag
            if 'node_id' not in slice_tag and slice_tag_check['node_id'] is not None:
                continue
            # do not compare between sliver tag and slice tag
            if 'node_id' in slice_tag and slice_tag['node_id'] is not None and slice_tag_check['node_id'] is None:
                continue
            if 'node_id' in slice_tag and slice_tag['node_id'] == slice_tag_check['node_id']:
                raise PLCInvalidArgument, "Sliver attribute already exists"
            if 'nodegroup_id' in slice_tag and slice_tag['nodegroup_id'] == slice_tag_check['nodegroup_id']:
                raise PLCInvalidArgument, "Slice attribute already exists for this nodegroup"
            if node_id_or_hostname is None and nodegroup_id_or_name is None:
                raise PLCInvalidArgument, "Slice attribute already exists"

        slice_tag.sync()
        self.event_objects = {'SliceTag': [slice_tag['slice_tag_id']]}

        return slice_tag['slice_tag_id']
