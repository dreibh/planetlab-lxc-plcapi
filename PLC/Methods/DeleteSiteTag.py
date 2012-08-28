#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.Sites import Site, Sites
from PLC.TagTypes import TagType, TagTypes
from PLC.SiteTags import SiteTag, SiteTags

# need to import so the core classes get decorated with caller_may_write_tag
from PLC.AuthorizeHelpers import AuthorizeHelpers

class DeleteSiteTag(Method):
    """
    Deletes the specified site setting

    Admins have full access.  Non-admins need to 
    (1) have at least one of the roles attached to the tagtype, 
    and (2) belong in the same site as the tagged subject.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        SiteTag.fields['site_tag_id']
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, site_tag_id):
        site_tags = SiteTags(self.api, [site_tag_id])
        if not site_tags:
            raise PLCInvalidArgument, "No such site tag %r"%site_tag_id
        site_tag = site_tags[0]

        tag_type_id = site_tag['tag_type_id']
        tag_type = TagTypes (self.api,[tag_type_id])[0]

        sites = Sites (self.api, site_tag['site_id'])
        if not sites:
            raise PLCInvalidArgument, "No such site %d"%site_tag['site_id']
        site=sites[0]
        
        # check authorizations
        site.caller_may_write_tag(self.api,self.caller,tag_type)

        site_tag.delete()
        self.object_ids = [site_tag['site_tag_id']]

        return 1
