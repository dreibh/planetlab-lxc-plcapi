#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.Persons import Person, Persons
from PLC.TagTypes import TagType, TagTypes
from PLC.PersonTags import PersonTag, PersonTags

# need to import so the core classes get decorated with caller_may_write_tag
from PLC.AuthorizeHelpers import AuthorizeHelpers

class UpdatePersonTag(Method):
    """
    Updates the value of an existing person setting

    Admins have full access.  Non-admins can change their own tags.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    accepts = [
        Auth(),
        PersonTag.fields['person_tag_id'],
        PersonTag.fields['value']
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, person_tag_id, value):
        person_tags = PersonTags(self.api, [person_tag_id])
        if not person_tags:
            raise PLCInvalidArgument, "No such person setting %r"%person_tag_id
        person_tag = person_tags[0]

        tag_type_id = person_tag['tag_type_id']
        tag_type = TagTypes (self.api,[tag_type_id])[0]

        persons = Persons (self.api, person_tag['person_id'])
        if not persons:
            raise PLCInvalidArgument, "No such person %d"%person_tag['person_id']
        person=persons[0]

        # check authorizations
        person.caller_may_write_tag(self.api,self.caller,tag_type)

        person_tag['value'] = value
        person_tag.sync()

        self.object_ids = [person_tag['person_tag_id']]
        return 1
