import re

from PLC.Faults import *
from PLC.Auth import Auth
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Table import Row

from PLC.Slices import Slice, Slices
from PLC.Sites import Site, Sites
from PLC.TagTypes import TagTypes
from PLC.SliceTags import SliceTags
from PLC.Methods.AddSliceTag import AddSliceTag
from PLC.Methods.UpdateSliceTag import UpdateSliceTag

can_update = ['name', 'instantiation', 'url', 'description', 'max_nodes']

class AddSlice(Method):
    """
    Adds a new slice. Any fields specified in slice_fields are used,
    otherwise defaults are used.

    Valid slice names are lowercase and begin with the login_base
    (slice prefix) of a valid site, followed by a single
    underscore. Thereafter, only letters, numbers, or additional
    underscores may be used.

    PIs may only add slices associated with their own sites (i.e.,
    slice prefixes must always be the login_base of one of their
    sites).

    Returns the new slice_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin', 'pi']

    accepted_fields = Row.accepted_fields(can_update, Slice.fields)
    accepted_fields.update(Slice.tags)

    accepts = [
        Auth(),
        accepted_fields
        ]

    returns = Parameter(int, 'New slice_id (> 0) if successful')

    def call(self, auth, slice_fields):

        [native,tags,rejected]=Row.split_fields(slice_fields,[Slice.fields,Slice.tags])

        # type checking
        native = Row.check_fields (native, self.accepted_fields)
        if rejected:
            raise PLCInvalidArgument, "Cannot add Slice with column(s) %r"%rejected

        # Authenticated function
        assert self.caller is not None

        # 1. Lowercase.
        # 2. Begins with login_base (letters or numbers).
        # 3. Then single underscore after login_base.
        # 4. Then letters, numbers, or underscores.
        name = slice_fields['name']
        good_name = r'^[a-z0-9]+_[a-zA-Z0-9_]+$'
        if not name or \
           not re.match(good_name, name):
            raise PLCInvalidArgument, "Invalid slice name"

        # Get associated site details
        login_base = name.split("_")[0]
        sites = Sites(self.api, [login_base])
        if not sites:
            raise PLCInvalidArgument, "Invalid slice prefix %s in %s"%(login_base,name)
        site = sites[0]

        if 'admin' not in self.caller['roles']:
            if site['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Slice prefix %s must match one of your sites' login_base"%login_base

        if len(site['slice_ids']) >= site['max_slices']:
            raise PLCInvalidArgument, \
                "Site %s has reached (%d) its maximum allowable slice count (%d)"%(site['name'],
                                                                                   len(site['slice_ids']),
                                                                                   site['max_slices'])
        if not site['enabled']:
            raise PLCInvalidArgument, "Site %s is disabled and can cannot create slices" % (site['name'])

        slice = Slice(self.api, native)
        slice['creator_person_id'] = self.caller['person_id']
        slice['site_id'] = site['site_id']
        slice.sync()

        for (tagname,value) in tags.iteritems():
            # the tagtype instance is assumed to exist, just check that
            if not TagTypes(self.api,{'tagname':tagname}):
                raise PLCInvalidArgument,"No such TagType %s"%tagname
            slice_tags=SliceTags(self.api,{'tagname':tagname,'slice_id':slice['slice_id']})
            if not slice_tags:
                AddSliceTag(self.api).__call__(auth,slice['slice_id'],tagname,value)
            else:
                UpdateSliceTag(self.api).__call__(auth,slice_tags[0]['slice_tag_id'],value)

        # take PLC_VSYS_DEFAULTS into account for convenience
        try:
            values= [ y for y in [ x.strip() for x in self.api.config.PLC_VSYS_DEFAULTS.split(',') ] if y ]
            for value in values:
                AddSliceTag(self.api).__call__(auth,slice['slice_id'],'vsys',value)
        except:
            print "Could not set vsys tags as configured in PLC_VSYS_DEFAULTS"
            import traceback
            traceback.print_exc()
        self.event_objects = {'Slice': [slice['slice_id']]}
        self.message = "Slice %d created" % slice['slice_id']

        return slice['slice_id']
