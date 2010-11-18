#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Table import Row, Table
from PLC.Interfaces import Interface, Interfaces
from PLC.TagTypes import TagType, TagTypes

class Ilink(Row):
    """
    Representation of a row in the ilink table.
    To use, instantiate with a dict of values.
    """

    table_name = 'ilink'
    primary_key = 'ilink_id'
    fields = {
        'ilink_id': Parameter(int, "ilink identifier"),
        'tag_type_id': TagType.fields['tag_type_id'],
        'src_interface_id': Parameter(int, "source interface identifier"),
        'dst_interface_id': Parameter(int, "destination interface identifier"),
        'value': Parameter( str, "optional ilink value"),
        }

class Ilinks(Table):
    """
    Representation of row(s) from the ilink table in the
    database.
    """

    def __init__(self, api, ilink_filter = None, columns = None):
        Table.__init__(self, api, Ilink, columns)

        sql = "SELECT %s FROM view_ilinks WHERE True" % \
              ", ".join(self.columns)

        if ilink_filter is not None:
            if isinstance(ilink_filter, (list, tuple, set, int, long)):
                ilink_filter = Filter(Ilink.fields, {'ilink_id': ilink_filter})
            elif isinstance(ilink_filter, dict):
                ilink_filter = Filter(Ilink.fields, ilink_filter)
            else:
                raise PLCInvalidArgument, "Wrong ilink filter %r"%ilink_filter
            sql += " AND (%s) %s" % ilink_filter.sql(api)


        self.selectall(sql)
