from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Auth import PasswordAuth

class GetPersons(Method):
    """
    Return an array of structs containing details about accounts. If
    person_id_or_email_list is specified, only the specified accounts
    will be queried.

    Users and techs may only retrieve details about themselves. PIs
    may retrieve details about themselves and others at their
    sites. Admins may retrieve details about all accounts.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        [Mixed(Person.fields['person_id'],
               Person.fields['email'])],
        Parameter([str], 'List of fields to return')
        ]

    # Filter out password field
    can_return = lambda (field, value): field not in ['password']
    return_fields = dict(filter(can_return, Person.fields.items()))
    returns = [return_fields]

    def call(self, auth, person_id_or_email_list = None):
	# If we are not admin, make sure to only return viewable accounts
        if 'admin' not in self.caller['roles']:
            # Get accounts that we are able to view
            valid_person_ids = [self.caller['person_id']]
            if 'pi' in self.caller['roles'] and self.caller['site_ids']:
                sites = Sites(self.api, self.caller['site_ids']).values()
                for site in sites:
                    valid_person_ids += site['person_ids']

            if not valid_person_ids:
                return []

            if not person_id_or_email_list:
                person_id_or_email_list = valid_person_ids

        persons = Persons(self.api, person_id_or_email_list).values()

        # Filter out accounts that are not viewable
        if 'admin' not in self.caller['roles']:
            persons = filter(self.caller.can_view, persons)

        return persons
