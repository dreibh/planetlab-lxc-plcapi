#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.TagTypes import TagTypes, TagType
from PLC.Nodes import Node
from PLC.Slices import Slice, Slices
from PLC.SliceTags import SliceTag, SliceTags
from PLC.InitScripts import InitScript, InitScripts

from PLC.AuthorizeHelpers import AuthorizeHelpers

# need to import so the core classes get decorated with caller_may_write_tag
from PLC.AuthorizeHelpers import AuthorizeHelpers

class UpdateSliceTag(Method):
    """
    Updates the value of an existing slice or sliver attribute.

    Users may only update attributes of slices or slivers of which
    they are members. PIs may only update attributes of slices or
    slivers at their sites, or of which they are members. Admins may
    update attributes of any slice or sliver.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user', 'node']

    accepts = [
        Auth(),
        SliceTag.fields['slice_tag_id'],
        Mixed(SliceTag.fields['value'],
              InitScript.fields['name'])
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, slice_tag_id, value):
        slice_tags = SliceTags(self.api, [slice_tag_id])
        if not slice_tags:
            raise PLCInvalidArgument, "No such slice attribute"
        slice_tag = slice_tags[0]

        tag_type_id = slice_tag['tag_type_id']
        tag_type = TagTypes (self.api,[tag_type_id])[0]

        slices = Slices(self.api, [slice_tag['slice_id']])
        if not slices:
            raise PLCInvalidArgument, "No such slice %d"%slice_tag['slice_id']
        slice = slices[0]

        assert slice_tag['slice_tag_id'] in slice['slice_tag_ids']

        # check authorizations
        node_id_or_hostname=slice_tag['node_id']
        nodegroup_id_or_name=slice_tag['nodegroup_id']
        slice.caller_may_write_tag(self.api,self.caller,tag_type,node_id_or_hostname,nodegroup_id_or_name)

        if slice_tag['tagname'] in ['initscript']:
            initscripts = InitScripts(self.api, {'enabled': True, 'name': value})
            if not initscripts:
                raise PLCInvalidArgument, "No such plc initscript"

        slice_tag['value'] = unicode(value)
        slice_tag.sync()
        self.event_objects = {'SliceTag': [slice_tag['slice_tag_id']]}
        return 1
