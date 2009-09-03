# $Id$
# $URL$
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Sites import Site, Sites
from PLC.Auth import Auth
from PLC.SFA import SFA

class AddPersonToSite(Method):
    """
    Adds the specified person to the specified site. If the person is
    already a member of the site, no errors are returned. Does not
    change the person's primary site.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email']),
        Mixed(Site.fields['site_id'],
              Site.fields['login_base'])
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, person_id_or_email, site_id_or_login_base):
        # Get account information
        persons = Persons(self.api, [person_id_or_email])
        if not persons:
            raise PLCInvalidArgument, "No such account"
        person = persons[0]

        if person['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local account"

        # Get site information
        sites = Sites(self.api, [site_id_or_login_base])
        if not sites:
            raise PLCInvalidArgument, "No such site"
        site = sites[0]

        if site['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local site"

        if site['site_id'] not in person['site_ids']:
            site.add_person(person)

        # Logging variables
        self.event_objects = {'Site': [site['site_id']],
                              'Person': [person['person_id']]}
        self.message = 'Person %d added to site %d' % \
                       (person['person_id'], site['site_id'])

        sfa = SFA(self.api)
        sfa.update_record(person, 'user')

        return 1
