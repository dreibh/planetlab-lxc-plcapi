#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth

from PLC.SiteTags import SiteTag, SiteTags
from PLC.Sites import Site, Sites

class GetSiteTags(Method):
    """
    Returns an array of structs containing details about
    sites and related settings.

    If site_tag_filter is specified and is an array of
    site setting identifiers, only site settings matching
    the filter will be returned. If return_fields is specified, only
    the specified details will be returned.
    """

    roles = ['admin', 'pi', 'user', 'node']

    accepts = [
        Auth(),
        Mixed([SiteTag.fields['site_tag_id']],
              Parameter(int,"Site setting id"),
              Filter(SiteTag.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [SiteTag.fields]


    def call(self, auth, site_tag_filter = None, return_fields = None):

        site_tags = SiteTags(self.api, site_tag_filter, return_fields)

        return site_tags
