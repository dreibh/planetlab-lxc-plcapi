import os

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Auth import PasswordAuth

class GetPersons(Method):
    """
    Return an array of dictionaries containing details about the
    specified accounts.

    ins may retrieve details about all accounts by not specifying
    person_id_or_email_list or by specifying an empty list. Users and
    techs may only retrieve details about themselves. PIs may retrieve
    details about themselves and others at their sites.

    If return_fields is specified, only the specified fields will be
    returned, if set. Otherwise, the default set of fields returned is:

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

    def __init__(self, *args, **kwds):
        Method.__init__(self, *args, **kwds)
        # Update documentation with list of default fields returned
        self.__doc__ += os.linesep.join(self.return_fields.keys())

    def call(self, auth, person_id_or_email_list = None, return_fields = None):
        # Make sure that only valid fields are specified
        if return_fields is None:
            return_fields = self.return_fields
        elif filter(lambda field: field not in self.return_fields, return_fields):
            raise PLCInvalidArgument, "Invalid return field specified"

        # Authenticated function
        assert self.caller is not None

        # Only admins can not specify person_id_or_email_list or
        # specify an empty list.
        if not person_id_or_email_list and 'admin' not in self.caller['roles']:
            raise PLCInvalidArgument, "List of accounts to retrieve not specified"

        # Get account information
        persons = Persons(self.api, person_id_or_email_list)

        # Filter out accounts that are not viewable and turn into list
        persons = filter(self.caller.can_view, persons.values())

        # Turn each person into a real dict.
        persons = [dict(person.items()) for person in persons]
                    
        return persons
