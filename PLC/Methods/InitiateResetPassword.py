from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Messages import Message, Messages
from PLC.Auth import AnonymousAuth

import os
import time
from random import Random
import string

def create_random_string():
    """
    create and return a random string.
    """
    random = Random()
    pool = string.letters + string.digits
    key = [random.choice(pool) for i in range(32)]
    random.shuffle(key) 
    key = ''.join(key)
	
    return key    

class InitiateResetPassword(Method):
    """
    start the reset password procedure. this sends the user an email
    they can use to go to the web interface to finish the reset of their
    password.

    the password is not modified yet. A random link to a password reset page
    is created, and set to expire in 24 hours.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        AnonymousAuth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email'])
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, person_id_or_email):

        # Get account information
        persons = Persons(self.api, [person_id_or_email])
        if not persons:
            raise PLCInvalidArgument, "No such account"
        
	# update the verification key for this person in the db
	person = persons[0]
	verification_key = create_random_string()
        person['verification_key'] = verification_key
        person['verification_expires'] = \
            time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time()+86400))
        person.sync()
	
	# send notification email
	person.send_initiate_password_reset_email()

	# Logging variables
        self.object_ids = [person['person_id']]
        self.message = 'Initiated password reset for person %d.' % \
                (person['person_id'])
 
        return 1
