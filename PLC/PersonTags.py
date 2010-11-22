#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Filter import Filter
from PLC.Table import Row, Table
from PLC.TagTypes import TagType, TagTypes
from PLC.Persons import Person

class PersonTag(Row):
    """
    Representation of a row in the person_tag.
    To use, instantiate with a dict of values.
    """

    table_name = 'person_tag'
    primary_key = 'person_tag_id'
    fields = {
        'person_tag_id': Parameter(int, "Person setting identifier"),
        'person_id': Person.fields['person_id'],
        'email': Person.fields['email'],
        'tag_type_id': TagType.fields['tag_type_id'],
        'tagname': TagType.fields['tagname'],
        'description': TagType.fields['description'],
        'category': TagType.fields['category'],
        'value': Parameter(str, "Person setting value"),
        ### relations

        }

class PersonTags(Table):
    """
    Representation of row(s) from the person_tag table in the
    database.
    """

    def __init__(self, api, person_tag_filter = None, columns = None):
        Table.__init__(self, api, PersonTag, columns)

        sql = "SELECT %s FROM view_person_tags WHERE True" % \
              ", ".join(self.columns)

        if person_tag_filter is not None:
            if isinstance(person_tag_filter, (list, tuple, set, int, long)):
                person_tag_filter = Filter(PersonTag.fields, {'person_tag_id': person_tag_filter})
            elif isinstance(person_tag_filter, dict):
                person_tag_filter = Filter(PersonTag.fields, person_tag_filter)
            else:
                raise PLCInvalidArgument, "Wrong person setting filter %r"%person_tag_filter
            sql += " AND (%s) %s" % person_tag_filter.sql(api)


        self.selectall(sql)
