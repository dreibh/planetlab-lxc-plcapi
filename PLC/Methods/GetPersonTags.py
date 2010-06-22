# $Id: GetPersonTags.py 14587 2009-07-19 13:18:50Z thierry $
# $URL: http://svn.planet-lab.org/svn/PLCAPI/tags/PLCAPI-4.3-27/PLC/Methods/GetPersonTags.py $
#
# Thierry Parmentelat - INRIA
#
# $Revision: 14587 $
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth

from PLC.PersonTags import PersonTag, PersonTags

class GetPersonTags(Method):
    """
    Returns an array of structs containing details about
    persons and related settings.

    If person_tag_filter is specified and is an array of
    person setting identifiers, only person settings matching
    the filter will be returned. If return_fields is specified, only
    the specified details will be returned.
    """

    roles = ['admin', 'pi', 'user', 'node']

    accepts = [
        Auth(),
        Mixed([PersonTag.fields['person_tag_id']],
              Parameter(int,"Person setting id"),
              Filter(PersonTag.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [PersonTag.fields]


    def call(self, auth, person_tag_filter = None, return_fields = None):

        person_tags = PersonTags(self.api, person_tag_filter, return_fields)

        return person_tags
