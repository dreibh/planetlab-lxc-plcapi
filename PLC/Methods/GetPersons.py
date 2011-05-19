from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Persons import Person, Persons
from PLC.Sites import Site, Sites
from PLC.Auth import Auth

hidden_fields = ['password', 'verification_key', 'verification_expires']

class GetPersons(Method):
    """
    Returns an array of structs containing details about users. If
    person_filter is specified and is an array of user identifiers or
    usernames, or a struct of user attributes, only users matching the
    filter will be returned. If return_fields is specified, only the
    specified details will be returned.

    Users and techs may only retrieve details about themselves. PIs
    may retrieve details about themselves and others at their
    sites. Admins and nodes may retrieve details about all accounts.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node']

    accepts = [
        Auth(),
        Mixed([Mixed(Person.fields['person_id'],
                     Person.fields['email'])],
              Parameter(str,"email"),
              Parameter(int,"person_id"),
              Filter(Person.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    # Filter out password field
    return_fields = dict(filter(lambda (field, value): field not in hidden_fields,
                                Person.fields.items()))
    returns = [return_fields]

    def call(self, auth, person_filter = None, return_fields = None):
        # If we are not admin, make sure to only return viewable accounts
        if isinstance(self.caller, Person) and \
           'admin' not in self.caller['roles']:
            # Get accounts that we are able to view
            valid_person_ids = [self.caller['person_id']]
            if ('pi' in self.caller['roles'] or 'tech' in self.caller['roles']) \
               and self.caller['site_ids']:
                sites = Sites(self.api, self.caller['site_ids'])
                for site in sites:
                    valid_person_ids += site['person_ids']
            if not valid_person_ids:
                return []

            # this may look suspicious; what if person_filter is not None ?
            # turns out the results are getting filtered again below, so we're safe
            # although this part of the code does not always trigger, it's probably 
            # a sensible performance enhancement for all the times 
            # when GetPersons() gets called without an argument
            if person_filter is None:
                person_filter = valid_person_ids

        # Filter out password field
        if return_fields:
            return_fields = filter(lambda field: field not in hidden_fields,
                                   return_fields)
        else:
            return_fields = self.return_fields.keys()

        # Must query at least person_id, site_ids, and role_ids (see
        # Person.can_view() and below).
        if return_fields is not None:
            added_fields = set(['person_id', 'site_ids', 'role_ids','roles']).difference(return_fields)
            return_fields += added_fields
        else:
            added_fields = []

        persons = Persons(self.api, person_filter, return_fields)

        # Filter out accounts that are not viewable
        if isinstance(self.caller, Person) and \
           'admin' not in self.caller['roles']:
            persons = filter(self.caller.can_view, persons)

        # Remove added fields if not specified
        if added_fields:
            for person in persons:
                for field in added_fields:
                    if field in person:
                        del person[field]

        return persons
