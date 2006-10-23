from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Auth import PasswordAuth

class AdmQueryPerson(Method):
    """
    Deprecated. See GetPersons.
    """

    status = "deprecated"

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        {'email': Person.fields['email']}
        ]

    returns = [Person.fields['person_id']]

    def call(self, auth, search_vals):
        if 'email' in search_vals:
            persons = Persons(self.api, [search_vals['email']]).values()
            if persons:
                return [persons[0]['person_id']]

        return []
