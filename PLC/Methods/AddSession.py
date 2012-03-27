import time

from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth
from PLC.Sessions import Session, Sessions
from PLC.Persons import Person, Persons

class AddSession(Method):
    """
    Creates and returns a new session key for the specified user.
    (Used for website 'user sudo')
    """

    roles = ['admin']
    accepts = [
        Auth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email'])
        ]
    returns = Session.fields['session_id']


    def call(self, auth, person_id_or_email):

        persons = Persons(self.api, [person_id_or_email], ['person_id', 'email'])

        if not persons:
            raise PLCInvalidArgument, "No such person"

        person = persons[0]
        session = Session(self.api)
        session['expires'] = int(time.time()) + (24 * 60 * 60)
        session.sync(commit = False)
        session.add_person(person, commit = True)

        return session['session_id']
