#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.PersonTags import PersonTag, PersonTags
from PLC.Persons import Person, Persons

from PLC.AuthorizeHelpers import AuthorizeHelpers

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

        person = Persons (self.api, person_tag['person_id'])[0]

        # check authorizations
        if 'admin' in self.caller['roles']:
            pass
        # user can change tags on self
        elif AuthorizeHelpers.person_may_access_person (self.api, self.caller, person):
            pass
        else:
            raise PLCPermissionDenied, "%s: you can only change your own tags"%self.name

        person_tag.delete()
        self.object_ids = [person_tag['person_tag_id']]

        return 1
