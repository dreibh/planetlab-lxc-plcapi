from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Messages import Message, Messages
from PLC.Auth import AnonymousAuth

import time

class VerifyPerson(Method):
    """
    Check that the verification_key is valid for a specified person
    and not expired. 

    Returns 1 if the verification key if valid.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        AnonymousAuth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email']),
	Person.fields['verification_key']
        ]

    returns = Parameter(int, '1 if verification_key is valid')

    def call(self, auth, person_id_or_email, verification_key):

	# Get account information
        persons = Persons(self.api, [person_id_or_email])
        if not persons:
            raise PLCInvalidArgument, "No such account"

        person = persons[0]

	# make sure verification key matches
	if not person['verification_key']:
	    raise PLCInvalidArgument, "Invalid key"
	if person['verification_key'] != verification_key:
	    raise PLCInvalidArgument, "Invalid key"

	# make sure key is not expired
	if not person['verification_expires']:
	    raise PLCInvalidArgument, "Invalid key"
	expires = str(person['verification_expires'])
        if time.strptime(expires, "%Y-%m-%d %H:%M:%S") < \
           time.gmtime(time.time()):
            raise PLCInvalidArgument, "Invalid key"
	
	# Logging variables
        self.object_ids = [person['person_id']]
        self.message = 'Verification key check on perons %d.' % \
                (person['person_id'])
 
        return 1
