# $Id: AddSiteTag.py 14587 2009-07-19 13:18:50Z thierry $
# $URL: http://svn.planet-lab.org/svn/PLCAPI/tags/PLCAPI-4.3-27/PLC/Methods/AddSiteTag.py $
#
# Thierry Parmentelat - INRIA
#
# $Revision: 14587 $
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.TagTypes import TagType, TagTypes
from PLC.SiteTags import SiteTag, SiteTags
from PLC.Sites import Site, Sites

from PLC.Nodes import Nodes
from PLC.Sites import Sites

class AddSiteTag(Method):
    """
    Sets the specified setting for the specified site
    to the specified value.

    In general only tech(s), PI(s) and of course admin(s) are allowed to
    do the change, but this is defined in the tag type object.

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

    object_type = 'Site'


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

	# check permission : it not admin, is the user affiliated with the right site
	if 'admin' not in self.caller['roles']:
	    # locate site
	    site = Sites (self.api, site_id)[0]
	    # check caller is affiliated with this site
	    if self.caller['person_id'] not in site['person_ids']:
		raise PLCPermissionDenied, "Not a member of the hosting site %s"%site['abbreviated_site']
	    
	    required_min_role = tag_type ['min_role_id']
	    if required_min_role is not None and \
		    min(self.caller['role_ids']) > required_min_role:
		raise PLCPermissionDenied, "Not allowed to modify the specified site setting, requires role %d",required_min_role

        site_tag = SiteTag(self.api)
        site_tag['site_id'] = site['site_id']
        site_tag['tag_type_id'] = tag_type['tag_type_id']
        site_tag['value'] = value

        site_tag.sync()
	self.object_ids = [site_tag['site_tag_id']]

        return site_tag['site_tag_id']
