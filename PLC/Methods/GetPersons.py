from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Persons import Person, Persons
from PLC.Auth import Auth

class GetPersons(Method):
    """
    Returns an array of structs containing details about users. If
    person_filter is specified and is an array of user identifiers or
    usernames, or a struct of user attributes, only users matching the
    filter will be returned. If return_fields is specified, only the
    specified details will be returned.

    Users and techs may only retrieve details about themselves. PIs
    may retrieve details about themselves and others at their
    sites. Admins may retrieve details about all accounts.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        Auth(),
        Mixed([Mixed(Person.fields['person_id'],
                     Person.fields['email'])],
              Filter(Person.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    # Filter out password field
    can_return = lambda (field, value): field not in ['password']
    return_fields = dict(filter(can_return, Person.fields.items()))
    returns = [return_fields]

    def call(self, auth, person_filter = None, return_fields = None):
	# If we are not admin, make sure to only return viewable accounts
        if 'admin' not in self.caller['roles']:
            # Get accounts that we are able to view
            valid_person_ids = [self.caller['person_id']]
            if 'pi' in self.caller['roles'] and self.caller['site_ids']:
                sites = Sites(self.api, self.caller['site_ids'])
                for site in sites:
                    valid_person_ids += site['person_ids']

            if not valid_person_ids:
                return []

            if person_filter is None:
                person_filter = valid_person_ids

        # Filter out password field
        if return_fields:
            while 'password' in return_fields:
                return_fields.remove('password')

        persons = Persons(self.api, person_filter, return_fields)

        # Filter out accounts that are not viewable
        if 'admin' not in self.caller['roles']:
            persons = filter(self.caller.can_view, persons)

        return persons
