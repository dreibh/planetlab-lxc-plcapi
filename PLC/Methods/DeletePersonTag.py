# $Id: DeletePersonTag.py 14587 2009-07-19 13:18:50Z thierry $
# $URL: http://svn.planet-lab.org/svn/PLCAPI/tags/PLCAPI-4.3-27/PLC/Methods/DeletePersonTag.py $
#
# Thierry Parmentelat - INRIA
#
# $Revision: 14587 $
#

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.PersonTags import PersonTag, PersonTags
from PLC.Persons import Person, Persons

from PLC.Nodes import Node, Nodes
from PLC.Persons import Person, Persons

class DeletePersonTag(Method):
    """
    Deletes the specified person setting

    Attributes may require the caller to have a particular role in order
    to be deleted, depending on the related tag type.
    Admins may delete attributes of any slice or sliver.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        PersonTag.fields['person_tag_id']
        ]

    returns = Parameter(int, '1 if successful')

    object_type = 'Person'


    def call(self, auth, person_tag_id):
        person_tags = PersonTags(self.api, [person_tag_id])
        if not person_tags:
            raise PLCInvalidArgument, "No such person tag %r"%person_tag_id
        person_tag = person_tags[0]

        ### reproducing a check from UpdateSliceTag, looks dumb though
        persons = Persons(self.api, [person_tag['person_id']])
        if not persons:
            raise PLCInvalidArgument, "No such person %r"%person_tag['person_id']
        person = persons[0]

        assert person_tag['person_tag_id'] in person['person_tag_ids']

	# check permission : it not admin, is the user affiliated with the right person
	if 'admin' not in self.caller['roles']:
	    # check caller is affiliated with this person's site
	    if len(set(person['site_ids']) & set(self.caller['site_ids'])) == 0:
		raise PLCPermissionDenied, "Not a member of the person's sites: %s"%person['site_ids']
	    
	    required_min_role = tag_type ['min_role_id']
	    if required_min_role is not None and \
		    min(self.caller['role_ids']) > required_min_role:
		raise PLCPermissionDenied, "Not allowed to modify the specified person setting, requires role %d",required_min_role

        person_tag.delete()
	self.object_ids = [person_tag['person_tag_id']]

        return 1
