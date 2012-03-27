#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Table import Row, Table
from PLC.TagTypes import TagType, TagTypes
from PLC.Interfaces import Interface

class InterfaceTag(Row):
    """
    Representation of a row in the interface_tag.
    To use, instantiate with a dict of values.
    """

    table_name = 'interface_tag'
    primary_key = 'interface_tag_id'
    fields = {
        'interface_tag_id': Parameter(int, "Interface setting identifier"),
        'interface_id': Interface.fields['interface_id'],
        'ip': Interface.fields['ip'],
        'tag_type_id': TagType.fields['tag_type_id'],
        'tagname': TagType.fields['tagname'],
        'description': TagType.fields['description'],
        'category': TagType.fields['category'],
        'value': Parameter(str, "Interface setting value"),
        ### relations

        }

class InterfaceTags(Table):
    """
    Representation of row(s) from the interface_tag table in the
    database.
    """

    def __init__(self, api, interface_tag_filter = None, columns = None):
        Table.__init__(self, api, InterfaceTag, columns)

        sql = "SELECT %s FROM view_interface_tags WHERE True" % \
              ", ".join(self.columns)

        if interface_tag_filter is not None:
            if isinstance(interface_tag_filter, (list, tuple, set, int, long)):
                interface_tag_filter = Filter(InterfaceTag.fields, {'interface_tag_id': interface_tag_filter})
            elif isinstance(interface_tag_filter, dict):
                interface_tag_filter = Filter(InterfaceTag.fields, interface_tag_filter)
            else:
                raise PLCInvalidArgument, "Wrong interface setting filter %r"%interface_tag_filter
            sql += " AND (%s) %s" % interface_tag_filter.sql(api)


        self.selectall(sql)
