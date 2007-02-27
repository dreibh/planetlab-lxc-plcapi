from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.Persons import Person, Persons
from PLC.sendmail import sendmail

class NotifyPersons(Method):
    """
    Sends an e-mail message to the specified users. If person_filter
    is specified and is an array of user identifiers or usernames, or
    a struct of user attributes, only users matching the filter will
    receive the message.

    Returns 1 if successful.
    """

    roles = ['admin', 'node']

    accepts = [
        Auth(),
        Mixed([Mixed(Person.fields['person_id'],
                     Person.fields['email'])],
              Filter(Person.fields)),
        Parameter(str, "E-mail subject"),
        Parameter(str, "E-mail body")
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, person_filter, subject, body):
        persons = Persons(self.api, person_filter,
                          ['person_id', 'first_name', 'last_name', 'email'])
        if not persons:
            raise PLCInvalidArgument, "No such user(s)"

        # Send email
        sendmail(self.api,
                 To = [("%s %s" % (person['first_name'], person['last_name']),
                        person['email']) for person in persons],
                 Subject = subject,
                 Body = body)

        # Logging variables
        self.event_objects = {'Person': [person['person_id'] for person in persons]}
        self.message = subject

        return 1
