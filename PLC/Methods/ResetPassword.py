import random
import base64
import time
import urllib

from types import StringTypes

from PLC.Debug import log
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Messages import Message, Messages
from PLC.Auth import Auth
from PLC.sendmail import sendmail

class ResetPassword(Method):
    """
    If verification_key is not specified, then a new verification_key
    will be generated and stored with the user's account. The key will
    be e-mailed to the user in the form of a link to a web page.

    The web page should verify the key by calling this function again
    and specifying verification_key. If the key matches what has been
    stored in the user's account, a new random password will be
    e-mailed to the user.

    Returns 1 if verification_key was not specified, or was specified
    and is valid, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email']),
        Person.fields['verification_key'],
        Person.fields['verification_expires']
        ]

    returns = Parameter(int, '1 if verification_key is valid')

    def call(self, auth, person_id_or_email, verification_key = None, verification_expires = None):
        # Get account information
        # we need to search in local objects only
        if isinstance (person_id_or_email,StringTypes):
            filter={'email':person_id_or_email}
        else:
            filter={'person_id':person_id_or_email}
        filter['peer_id']=None
        persons = Persons(self.api, filter)
        if not persons:
            raise PLCInvalidArgument, "No such account"
        person = persons[0]

        if person['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local account"

        if not person['enabled']:
            raise PLCInvalidArgument, "Account must be enabled"

        # Be paranoid and deny password resets for admins
        if 'admin' in person['roles']:
            raise PLCInvalidArgument, "Cannot reset admin passwords"

        # Generate 32 random bytes
        bytes = random.sample(xrange(0, 256), 32)
        # Base64 encode their string representation
        random_key = base64.b64encode("".join(map(chr, bytes)))

        if verification_key is not None:
            if person['verification_key'] is None or \
               person['verification_expires'] is None or \
               person['verification_expires'] < time.time():
                raise PLCPermissionDenied, "Verification key has expired"
            elif person['verification_key'] != verification_key:
                raise PLCPermissionDenied, "Verification key incorrect"
            else:
                # Reset password to random string
                person['password'] = random_key
                person['verification_key'] = None
                person['verification_expires'] = None
                person.sync()

                message_id = 'Password reset'
        else:
            # Only allow one reset at a time
            if person['verification_expires'] is not None and \
               person['verification_expires'] > time.time():
                raise PLCPermissionDenied, "Password reset request already pending"

            if verification_expires is None:
                verification_expires = int(time.time() + (24 * 60 * 60))

            person['verification_key'] = random_key
            person['verification_expires'] = verification_expires
            person.sync()

            message_id = 'Password reset requested'

        messages = Messages(self.api, [message_id])
        if messages:
            # Send password to user
            message = messages[0]

            params = {'PLC_NAME': self.api.config.PLC_NAME,
                      'PLC_MAIL_SUPPORT_ADDRESS': self.api.config.PLC_MAIL_SUPPORT_ADDRESS,
                      'PLC_WWW_HOST': self.api.config.PLC_WWW_HOST,
                      'PLC_WWW_SSL_PORT': self.api.config.PLC_WWW_SSL_PORT,
                      'person_id': person['person_id'],
                      # Will be used in a URL, so must quote appropriately
                      'verification_key': urllib.quote_plus(random_key),
                      'password': random_key,
                      'email': person['email']}

            sendmail(self.api,
                     To = ("%s %s" % (person['first_name'], person['last_name']), person['email']),
                     Subject = message['subject'] % params,
                     Body = message['template'] % params)
        else:
            print >> log, "Warning: No message template '%s'" % message_id

        # Logging variables
        self.event_objects = {'Person': [person['person_id']]}
        self.message = message_id

        return 1
