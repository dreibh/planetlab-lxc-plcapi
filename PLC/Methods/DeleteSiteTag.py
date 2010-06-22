# $Id: DeleteSiteTag.py 14587 2009-07-19 13:18:50Z thierry $
# $URL: http://svn.planet-lab.org/svn/PLCAPI/tags/PLCAPI-4.3-27/PLC/Methods/DeleteSiteTag.py $
#
# Thierry Parmentelat - INRIA
#
# $Revision: 14587 $
#

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.SiteTags import SiteTag, SiteTags
from PLC.Sites import Site, Sites

from PLC.Nodes import Node, Nodes
from PLC.Sites import Site, Sites

class DeleteSiteTag(Method):
    """
    Deletes the specified site setting

    Attributes may require the caller to have a particular role in order
    to be deleted, depending on the related tag type.
    Admins may delete attributes of any slice or sliver.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        SiteTag.fields['site_tag_id']
        ]

    returns = Parameter(int, '1 if successful')

    object_type = 'Site'


    def call(self, auth, site_tag_id):
        site_tags = SiteTags(self.api, [site_tag_id])
        if not site_tags:
            raise PLCInvalidArgument, "No such site tag %r"%site_tag_id
        site_tag = site_tags[0]

        ### reproducing a check from UpdateSliceTag, looks dumb though
        sites = Sites(self.api, [site_tag['site_id']])
        if not sites:
            raise PLCInvalidArgument, "No such site %r"%site_tag['site_id']
        site = sites[0]

        assert site_tag['site_tag_id'] in site['site_tag_ids']

        # check permission : it not admin, is the user affiliated with the right site
        if 'admin' not in self.caller['roles']:
            # check caller is affiliated with this site
            if self.caller['person_id'] not in site['person_ids']:
                raise PLCPermissionDenied, "Not a member of the hosting site %s"%site['abbreviated_site']

            required_min_role = tag_type ['min_role_id']
            if required_min_role is not None and \
                    min(self.caller['role_ids']) > required_min_role:
                raise PLCPermissionDenied, "Not allowed to modify the specified site setting, requires role %d",required_min_role

        site_tag.delete()
        self.object_ids = [site_tag['site_tag_id']]

        return 1
