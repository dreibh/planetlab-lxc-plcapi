# $Id$
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.SliceTags import SliceTag, SliceTags
from PLC.Slices import Slice, Slices
from PLC.InitScripts import InitScript, InitScripts
from PLC.Auth import Auth

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

        if 'admin' not in self.caller['roles']:
            if self.caller['person_id'] in slice['person_ids']:
                pass
            elif 'pi' not in self.caller['roles']:
                raise PLCPermissionDenied, "Not a member of the specified slice"
            elif slice['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Specified slice not associated with any of your sites"

            if slice_tag['min_role_id'] is not None and \
               min(self.caller['role_ids']) > slice_tag['min_role_id']:
                raise PLCPermissionDenied, "Not allowed to update the specified attribute"
	
	if slice_tag['tagname'] in ['initscript']:
            initscripts = InitScripts(self.api, {'enabled': True, 'name': value})
            if not initscripts:
                raise PLCInvalidArgument, "No such plc initscript"	

        slice_tag['value'] = unicode(value)
        slice_tag.sync()
	self.event_objects = {'SliceTag': [slice_tag['slice_tag_id']]}
        return 1
