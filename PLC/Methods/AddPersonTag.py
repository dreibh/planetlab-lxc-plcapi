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

from PLC.AuthorizeHelpers import AuthorizeHelpers

class AddPersonTag(Method):
    """
    Sets the specified setting for the specified person
    to the specified value.

    Admins have full access.  Non-admins can change their own tags.

    Returns the new person_tag_id (> 0) if successful, faults
    otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    accepts = [
        Auth(),
        # no other way to refer to a person
        PersonTag.fields['person_id'],
        Mixed(TagType.fields['tag_type_id'],
              TagType.fields['tagname']),
        PersonTag.fields['value'],
        ]

    returns = Parameter(int, 'New person_tag_id (> 0) if successful')

    def call(self, auth, person_id, tag_type_id_or_name, value):
        persons = Persons(self.api, [person_id])
        if not persons:
            raise PLCInvalidArgument, "No such person %r"%person_id
        person = persons[0]

        tag_types = TagTypes(self.api, [tag_type_id_or_name])
        if not tag_types:
            raise PLCInvalidArgument, "No such tag type %r"%tag_type_id_or_name
        tag_type = tag_types[0]

        # checks for existence - does not allow several different settings
        conflicts = PersonTags(self.api, {'person_id':person['person_id'],
                                          'tag_type_id':tag_type['tag_type_id']})

        if len(conflicts) :
            raise PLCInvalidArgument, "Person %d (%s) already has setting %d"% \
                (person['person_id'],person['email'], tag_type['tag_type_id'])

        # check authorizations
        if 'admin' in self.caller['roles']:
            pass
        # user can change tags on self
        elif AuthorizeHelpers.person_may_access_person (self.api, self.caller, person):
            pass
        else:
            raise PLCPermissionDenied, "%s: you can only change your own tags"%self.name


        person_tag = PersonTag(self.api)
        person_tag['person_id'] = person['person_id']
        person_tag['tag_type_id'] = tag_type['tag_type_id']
        person_tag['value'] = value

        person_tag.sync()
        self.object_ids = [person_tag['person_tag_id']]

        return person_tag['person_tag_id']
