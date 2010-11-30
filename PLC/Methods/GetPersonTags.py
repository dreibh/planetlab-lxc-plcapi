#
# Thierry Parmentelat - INRIA
#
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth

from PLC.Persons import Person, Persons
from PLC.PersonTags import PersonTag, PersonTags
from PLC.Sites import Sites, Site

class GetPersonTags(Method):
    """
    Returns an array of structs containing details about
    persons and related settings.

    If person_tag_filter is specified and is an array of
    person setting identifiers, only person settings matching
    the filter will be returned. If return_fields is specified, only
    the specified details will be returned.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        Auth(),
        Mixed([PersonTag.fields['person_tag_id']],
              Parameter(int,"Person setting id"),
              Filter(PersonTag.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [PersonTag.fields]


    def call(self, auth, person_tag_filter = None, return_fields = None):

        # only persons can call this (as per roles, but..)
        if not isinstance(self.caller,Person):
            return []

        # If we are not admin, make sure to only return viewable accounts
        valid_person_ids=None
        added_fields=[]
        if 'admin' not in self.caller['roles']:
            # Get accounts that we are able to view
            valid_person_ids = [self.caller['person_id']]
            if 'pi' in self.caller['roles'] and self.caller['site_ids']:
                sites = Sites(self.api, self.caller['site_ids'])
                for site in sites:
                    valid_person_ids += site['person_ids']

            if not valid_person_ids:
                return []
            
            # if we have to filter out on person_id, make sure this is returned from db
            if return_fields:
                added_fields = set(['person_id']).difference(return_fields)
                return_fields += added_fields

        person_tags = PersonTags(self.api, person_tag_filter, return_fields)
        
        if valid_person_ids is not None:
            person_tags = [ person_tag for person_tag in person_tags 
                            if person_tag['person_id'] in valid_person_ids]

        # Remove added fields if not initially specified
        if added_fields:
            for person_tag in person_tags:
                for field in added_fields:
                    if field in person_tag:
                        del person_tag[field]
        return person_tags
