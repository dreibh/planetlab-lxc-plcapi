#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.PersonTags import PersonTag, PersonTags
from PLC.Persons import Person, Persons

class DeletePersonTag(Method):
    """
    Deletes the specified person setting

    Admins have full access.  Non-admins can change their own tags.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        PersonTag.fields['person_tag_id']
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, person_tag_id):
        person_tags = PersonTags(self.api, [person_tag_id])
        if not person_tags:
            raise PLCInvalidArgument, "No such person tag %r"%person_tag_id
        person_tag = person_tags[0]

        persons = Persons (self.api, person_tag['person_id'])
        if not persons:
            raise PLCInvalidArgument, "No such person %d"%person_tag['person_id']
        person=persons[0]

        # check authorizations
        person.caller_may_write_tag(self.api,self.caller,tag_type)

        person_tag.delete()
        self.object_ids = [person_tag['person_tag_id']]

        return 1
