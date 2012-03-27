import time

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Table import Row
from PLC.Auth import Auth

from PLC.Slices import Slice, Slices
from PLC.Sites import Site, Sites
from PLC.TagTypes import TagTypes
from PLC.SliceTags import SliceTags
from PLC.Methods.AddSliceTag import AddSliceTag
from PLC.Methods.UpdateSliceTag import UpdateSliceTag

can_update = ['instantiation', 'url', 'description', 'max_nodes', 'expires']

class UpdateSlice(Method):
    """
    Updates the parameters of an existing slice with the values in
    slice_fields.

    Users may only update slices of which they are members. PIs may
    update any of the slices at their sites, or any slices of which
    they are members. Admins may update any slice.

    Only PIs and admins may update max_nodes. Slices cannot be renewed
    (by updating the expires parameter) more than 8 weeks into the
    future.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user']

    accepted_fields = Row.accepted_fields(can_update, Slice.fields)
    # xxx check the related_fields feature
    accepted_fields.update(Slice.related_fields)
    accepted_fields.update(Slice.tags)

    accepts = [
        Auth(),
        Mixed(Slice.fields['slice_id'],
              Slice.fields['name']),
        accepted_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, slice_id_or_name, slice_fields):

        # split provided fields
        [native,related,tags,rejected] = Row.split_fields(slice_fields,[Slice.fields,Slice.related_fields,Slice.tags])

        # type checking
        native = Row.check_fields (native, self.accepted_fields)
        if rejected:
            raise PLCInvalidArgument, "Cannot update Slice column(s) %r"%rejected

        slices = Slices(self.api, [slice_id_or_name])
        if not slices:
            raise PLCInvalidArgument, "No such slice %r"%slice_id_or_name
        slice = slices[0]

        if slice['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local slice"

        # Authenticated function
        assert self.caller is not None

        if 'admin' not in self.caller['roles']:
            if self.caller['person_id'] in slice['person_ids']:
                pass
            elif 'pi' not in self.caller['roles']:
                raise PLCPermissionDenied, "Not a member of the specified slice"
            elif slice['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Specified slice not associated with any of your sites"

        # Renewing
        renewing=False
        if 'expires' in slice_fields and slice_fields['expires'] > slice['expires']:
            sites = Sites(self.api, [slice['site_id']])
            assert sites
            site = sites[0]

            if site['max_slices'] <= 0:
                raise PLCInvalidArgument, "Slice creation and renewal have been disabled for the site"

            # Maximum expiration date is 8 weeks from now
            # XXX Make this configurable
            max_expires = time.time() + (8 * 7 * 24 * 60 * 60)

            if 'admin' not in self.caller['roles'] and slice_fields['expires'] > max_expires:
                raise PLCInvalidArgument, "Cannot renew a slice beyond 8 weeks from now"

            # XXX Make this a configurable policy
            if slice['description'] is None or not slice['description'].strip():
                if 'description' not in slice_fields or slice_fields['description'] is None or \
                   not slice_fields['description'].strip():
                    raise PLCInvalidArgument, "Cannot renew a slice with an empty description or URL"

            if slice['url'] is None or not slice['url'].strip():
                if 'url' not in slice_fields or slice_fields['url'] is None or \
                   not slice_fields['url'].strip():
                    raise PLCInvalidArgument, "Cannot renew a slice with an empty description or URL"
            renewing=True

        if 'max_nodes' in slice_fields and slice_fields['max_nodes'] != slice['max_nodes']:
            if 'admin' not in self.caller['roles'] and \
               'pi' not in self.caller['roles']:
                raise PLCInvalidArgument, "Only admins and PIs may update max_nodes"

        # Make requested associations
        for (k,v) in related.iteritems():
            slice.associate(auth,k,v)

        slice.update(slice_fields)
        slice.sync(commit=True)

        for (tagname,value) in tags.iteritems():
            # the tagtype instance is assumed to exist, just check that
            if not TagTypes(self.api,{'tagname':tagname}):
                raise PLCInvalidArgument,"No such TagType %s"%tagname
            slice_tags=SliceTags(self.api,{'tagname':tagname,'slice_id':slice['slice_id']})
            if not slice_tags:
                AddSliceTag(self.api).__call__(auth,slice['slice_id'],tagname,value)
            else:
                UpdateSliceTag(self.api).__call__(auth,slice_tags[0]['slice_tag_id'],value)

        self.event_objects = {'Slice': [slice['slice_id']]}
        if 'name' in slice:
            self.message='Slice %s updated'%slice['name']
        else:
            self.message='Slice %d updated'%slice['slice_id']
        if renewing:
            # it appears that slice['expires'] may be either an int, or a formatted string
            try:
                expire_date=time.strftime('%Y-%m-%d:%H:%M',time.localtime(float(slice['expires'])))
            except:
                expire_date=slice['expires']
            self.message += ' renewed until %s'%expire_date

        return 1
