#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.Sites import Site, Sites
from PLC.Nodes import Nodes
from PLC.TagTypes import TagType, TagTypes
from PLC.SiteTags import SiteTag, SiteTags

from PLC.AuthorizeHelpers import AuthorizeHelpers

class AddSiteTag(Method):
    """
    Sets the specified setting for the specified site
    to the specified value.

    Admins have full access.  Non-admins need to 
    (1) have at least one of the roles attached to the tagtype, 
    and (2) belong in the same site as the tagged subject.

    Returns the new site_tag_id (> 0) if successful, faults
    otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    accepts = [
        Auth(),
        # no other way to refer to a site
        SiteTag.fields['site_id'],
        Mixed(TagType.fields['tag_type_id'],
              TagType.fields['tagname']),
        SiteTag.fields['value'],
        ]

    returns = Parameter(int, 'New site_tag_id (> 0) if successful')

    def call(self, auth, site_id, tag_type_id_or_name, value):
        sites = Sites(self.api, [site_id])
        if not sites:
            raise PLCInvalidArgument, "No such site %r"%site_id
        site = sites[0]

        tag_types = TagTypes(self.api, [tag_type_id_or_name])
        if not tag_types:
            raise PLCInvalidArgument, "No such tag type %r"%tag_type_id_or_name
        tag_type = tag_types[0]

        # checks for existence - does not allow several different settings
        conflicts = SiteTags(self.api,
                             {'site_id':site['site_id'],
                              'tag_type_id':tag_type['tag_type_id']})

        if len(conflicts) :
            raise PLCInvalidArgument, "Site %d already has setting %d"%(site['site_id'],
                                                                        tag_type['tag_type_id'])

        # check authorizations
        if 'admin' in self.caller['roles']:
            pass
        elif not AuthorizeHelpers.person_access_tag_type (self.api, self.caller, tag_type):
            raise PLCPermissionDenied, "%s, no permission to use this tag type"%self.name
        elif AuthorizeHelpers.person_belongs_to_site (self.api, self.caller, site):
            pass
        else:
            raise PLCPermissionDenied, "%s: you must be part of the subject site"%self.name
            
        site_tag = SiteTag(self.api)
        site_tag['site_id'] = site['site_id']
        site_tag['tag_type_id'] = tag_type['tag_type_id']
        site_tag['value'] = value

        site_tag.sync()
        self.object_ids = [site_tag['site_tag_id']]

        return site_tag['site_tag_id']
