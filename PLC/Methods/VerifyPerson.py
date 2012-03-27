import random
import base64
import time
import urllib

from PLC.Debug import log
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Sites import Site, Sites
from PLC.Messages import Message, Messages
from PLC.Auth import Auth
from PLC.sendmail import sendmail

class VerifyPerson(Method):
    """
    Verify a new (must be disabled) user's e-mail address and registration.

    If verification_key is not specified, then a new verification_key
    will be generated and stored with the user's account. The key will
    be e-mailed to the user in the form of a link to a web page.

    The web page should verify the key by calling this function again
    and specifying verification_key. If the key matches what has been
    stored in the user's account, then an e-mail will be sent to the
    user's PI (and support if the user is requesting a PI role),
    asking the PI (or support) to enable the account.

    Returns 1 if the verification key if valid.
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
        persons = Persons(self.api, [person_id_or_email])
        if not persons:
            raise PLCInvalidArgument, "No such account %r"%person_id_or_email
        person = persons[0]

        if person['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local account %r"%person_id_or_email

        if person['enabled']:
            raise PLCInvalidArgument, "Account %r must be new (disabled)"%person_id_or_email

        # Get the primary site name
        person_sites = Sites(self.api, person['site_ids'])
        if person_sites:
            site_name = person_sites[0]['name']
        else:
            site_name = "No Site"

        # Generate 32 random bytes
        bytes = random.sample(xrange(0, 256), 32)
        # Base64 encode their string representation
        random_key = base64.b64encode("".join(map(chr, bytes)))

        if verification_key is None or \
        (verification_key is not None and person['verification_expires'] and \
        person['verification_expires'] < time.time()):
            # Only allow one verification at a time
            if person['verification_expires'] is not None and \
               person['verification_expires'] > time.time():
                raise PLCPermissionDenied, "Verification request already pending"

            if verification_expires is None:
                verification_expires = int(time.time() + (24 * 60 * 60))

            person['verification_key'] = random_key
            person['verification_expires'] = verification_expires
            person.sync()

            # Send e-mail to user
            To = ("%s %s" % (person['first_name'], person['last_name']), person['email'])
            Cc = None

            message_id = 'Verify account'


        elif verification_key is not None:
            if person['verification_key'] is None or \
               person['verification_expires'] is None:
                raise PLCPermissionDenied, "Invalid Verification key"
            elif person['verification_key'] != verification_key:
                raise PLCPermissionDenied, "Verification key incorrect"
            else:
                person['verification_key'] = None
                person['verification_expires'] = None
                person.sync()

                # Get the PI(s) of each site that the user is registering with
                person_ids = set()
                for site in person_sites:
                    person_ids.update(site['person_ids'])
                persons = Persons(self.api, person_ids)
                pis = filter(lambda person: 'pi' in person['roles'] and person['enabled'], persons)

                # Send e-mail to PI(s) and copy the user
                To = [("%s %s" % (pi['first_name'], pi['last_name']), pi['email']) for pi in pis]
                Cc = ("%s %s" % (person['first_name'], person['last_name']), person['email'])

                if 'pi' in person['roles']:
                    # And support if user is requesting a PI role
                    To.append(("%s Support" % self.api.config.PLC_NAME,
                               self.api.config.PLC_MAIL_SUPPORT_ADDRESS))
                    message_id = 'New PI account'
                else:
                    message_id = 'New account'

        messages = Messages(self.api, [message_id])
        if messages:
            # Send message to user
            message = messages[0]

            params = {'PLC_NAME': self.api.config.PLC_NAME,
                      'PLC_MAIL_SUPPORT_ADDRESS': self.api.config.PLC_MAIL_SUPPORT_ADDRESS,
                      'PLC_WWW_HOST': self.api.config.PLC_WWW_HOST,
                      'PLC_WWW_SSL_PORT': self.api.config.PLC_WWW_SSL_PORT,
                      'person_id': person['person_id'],
                      # Will be used in a URL, so must quote appropriately
                      'verification_key': urllib.quote_plus(random_key),
                      'site_name': site_name,
                      'first_name': person['first_name'],
                      'last_name': person['last_name'],
                      'email': person['email'],
                      'roles': ", ".join(person['roles'])}

            sendmail(self.api,
                     To = To,
                     Cc = Cc,
                     Subject = message['subject'] % params,
                     Body = message['template'] % params)
        else:
            print >> log, "Warning: No message template '%s'" % message_id

        # Logging variables
        self.event_objects = {'Person': [person['person_id']]}
        self.message = message_id

        if verification_key is not None and person['verification_expires'] and \
        person['verification_expires'] < time.time():
            raise PLCPermissionDenied, "Verification key has expired. Another email has been sent."

        return 1
