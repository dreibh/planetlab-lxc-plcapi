#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.SliceTags import SliceTag, SliceTags
from PLC.Nodes import Node
from PLC.Slices import Slice, Slices
from PLC.InitScripts import InitScript, InitScripts

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

        slices = Slices(self.api, [slice_tag['slice_id']])
        if not slices:
            raise PLCInvalidArgument, "No such slice"
        slice = slices[0]

        assert slice_tag['slice_tag_id'] in slice['slice_tag_ids']

        # check authorizations
        node_id_or_hostname=slice_tag['node_id']
        nodegroup_id_or_name=slice_tag['nodegroup_id']
        granted=False
        if 'admin' in self.caller['roles']:
            granted=True
        # does caller have right role(s) ? this knows how to deal with self.caller being a node
        elif not AuthorizeHelpers.caller_may_access_tag_type (self.api, self.caller, tag_type):
            granted=False
        # node callers: check the node is in the slice
        elif isinstance(self.caller, Node): 
            # nodes can only set their own sliver tags
            if node_id_or_hostname is None: 
                granted=False
            elif not AuthorizeHelpers.node_match_id (self.api, self.caller, node_id_or_hostname):
                granted=False
            elif not AuthorizeHelpers.node_in_slice (self.api, self.caller, slice):
                granted=False
        # caller is a non-admin person
        else:
            # only admins can handle slice tags on a nodegroup
            if nodegroup_id_or_name:
                raise PLCPermissionDenied, "%s, cannot set slice tag %s on nodegroup - restricted to admins"%\
                    (self.name,tag_type['tagname'])
            # if a node is specified it is expected to be in the slice
            if node_id_or_hostname:
                if not AuthorizeHelpers.node_id_in_slice (self.api, node_id_or_hostname, slice):
                    raise PLCPermissionDenied, "%s, node must be in slice when setting sliver tag"
            # try all roles to find a match - tech are ignored b/c not in AddSliceTag.roles anyways
            for role in AuthorizeHelpers.person_tag_type_common_roles(self.api,self.caller,tag_type):
                # regular users need to be in the slice
                if role=='user':
                    if AuthorizeHelpers.person_in_slice(self.api, self.caller, slice):
                        granted=True ; break
                # for convenience, pi's can tweak all the slices in their site
                elif role=='pi':
                    if AuthorizeHelpers.slice_belongs_to_pi (self.api, slice, self.caller):
                        granted=True ; break
        if not granted:
            raise PLCPermissionDenied, "%s, forbidden tag %s"%(self.name,tag_type['tagname'])

        if slice_tag['tagname'] in ['initscript']:
            initscripts = InitScripts(self.api, {'enabled': True, 'name': value})
            if not initscripts:
                raise PLCInvalidArgument, "No such plc initscript"

        slice_tag['value'] = unicode(value)
        slice_tag.sync()
        self.event_objects = {'SliceTag': [slice_tag['slice_tag_id']]}
        return 1
