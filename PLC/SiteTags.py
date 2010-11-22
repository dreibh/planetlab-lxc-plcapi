#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Table import Row, Table
from PLC.TagTypes import TagType, TagTypes
from PLC.Sites import Site

class SiteTag(Row):
    """
    Representation of a row in the site_tag.
    To use, instantiate with a dict of values.
    """

    table_name = 'site_tag'
    primary_key = 'site_tag_id'
    fields = {
        'site_tag_id': Parameter(int, "Site setting identifier"),
        'site_id': Site.fields['site_id'],
        'login_base': Site.fields['login_base'],
        'tag_type_id': TagType.fields['tag_type_id'],
        'tagname': TagType.fields['tagname'],
        'description': TagType.fields['description'],
        'category': TagType.fields['category'],
        'value': Parameter(str, "Site setting value"),
        ### relations

        }

class SiteTags(Table):
    """
    Representation of row(s) from the site_tag table in the
    database.
    """

    def __init__(self, api, site_tag_filter = None, columns = None):
        Table.__init__(self, api, SiteTag, columns)

        sql = "SELECT %s FROM view_site_tags WHERE True" % \
              ", ".join(self.columns)

        if site_tag_filter is not None:
            if isinstance(site_tag_filter, (list, tuple, set, int, long)):
                site_tag_filter = Filter(SiteTag.fields, {'site_tag_id': site_tag_filter})
            elif isinstance(site_tag_filter, dict):
                site_tag_filter = Filter(SiteTag.fields, site_tag_filter)
            else:
                raise PLCInvalidArgument, "Wrong site setting filter %r"%site_tag_filter
            sql += " AND (%s) %s" % site_tag_filter.sql(api)


        self.selectall(sql)
