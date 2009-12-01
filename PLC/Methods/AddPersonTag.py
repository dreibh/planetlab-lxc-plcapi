# $Id: AddPersonTag.py 14587 2009-07-19 13:18:50Z thierry $
# $URL: http://svn.planet-lab.org/svn/PLCAPI/tags/PLCAPI-4.3-27/PLC/Methods/AddPersonTag.py $
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
from PLC.PersonTags import PersonTag, PersonTags
from PLC.Persons import Person, Persons

from PLC.Nodes import Nodes

class AddPersonTag(Method):
    """
    Sets the specified setting for the specified person
    to the specified value.

    In general only tech(s), PI(s) and of course admin(s) are allowed to
    do the change, but this is defined in the tag type object.

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

    object_type = 'Person'


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
        conflicts = PersonTags(self.api,
                                        {'person_id':person['person_id'],
                                         'tag_type_id':tag_type['tag_type_id']})

        if len(conflicts) :
            raise PLCInvalidArgument, "Person %d already has setting %d"%(person['person_id'],
                                                                               tag_type['tag_type_id'])

	# check permission : it not admin, is the user affiliated with the same site as this person
	if 'admin' not in self.caller['roles']:
	    # check caller is affiliated with at least one of Person's sites
	    if len(set(person['site_ids']) & set(self.caller['site_ids'])) == 0:
		raise PLCPermissionDenied, "Not a member of the person's sites: %s"%person['site_ids']
	    
	    required_min_role = tag_type ['min_role_id']
	    if required_min_role is not None and \
		    min(self.caller['role_ids']) > required_min_role:
		raise PLCPermissionDenied, "Not allowed to modify the specified person setting, requires role %d",required_min_role

        person_tag = PersonTag(self.api)
        person_tag['person_id'] = person['person_id']
        person_tag['tag_type_id'] = tag_type['tag_type_id']
        person_tag['value'] = value

        person_tag.sync()
	self.object_ids = [person_tag['person_tag_id']]

        return person_tag['person_tag_id']
