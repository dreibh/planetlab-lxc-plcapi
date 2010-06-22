# $Id: UpdatePersonTag.py 14587 2009-07-19 13:18:50Z thierry $
# $URL: http://svn.planet-lab.org/svn/PLCAPI/tags/PLCAPI-4.3-27/PLC/Methods/UpdatePersonTag.py $
#
# $Revision: 14587 $
#

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.PersonTags import PersonTag, PersonTags
from PLC.Persons import Person, Persons

from PLC.Nodes import Nodes
from PLC.Persons import Persons

class UpdatePersonTag(Method):
    """
    Updates the value of an existing person setting

    Access rights depend on the tag type.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'tech', 'user']

    accepts = [
        Auth(),
        PersonTag.fields['person_tag_id'],
        PersonTag.fields['value']
        ]

    returns = Parameter(int, '1 if successful')

    object_type = 'Person'

    def call(self, auth, person_tag_id, value):
        person_tags = PersonTags(self.api, [person_tag_id])
        if not person_tags:
            raise PLCInvalidArgument, "No such person setting %r"%person_tag_id
        person_tag = person_tags[0]

        ### reproducing a check from UpdateSliceTag, looks dumb though
        persons = Persons(self.api, [person_tag['person_id']])
        if not persons:
            raise PLCInvalidArgument, "No such person %r"%person_tag['person_id']
        person = persons[0]

        assert person_tag['person_tag_id'] in person['person_tag_ids']

        # check permission : it not admin, is the user affiliated with the right person
        if 'admin' not in self.caller['roles']:
            # check caller is affiliated with this person's person
            if len(set(person['person_ids']) & set(self.caller['person_ids'])) == 0:
                raise PLCPermissionDenied, "Not a member of the person's persons: %s"%person['person_ids']

            required_min_role = tag_type ['min_role_id']
            if required_min_role is not None and \
                    min(self.caller['role_ids']) > required_min_role:
                raise PLCPermissionDenied, "Not allowed to modify the specified person setting, requires role %d",required_min_role

        person_tag['value'] = value
        person_tag.sync()

        self.object_ids = [person_tag['person_tag_id']]
        return 1
