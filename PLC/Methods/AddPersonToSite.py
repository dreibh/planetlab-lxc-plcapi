from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Sites import Site, Sites
from PLC.Auth import PasswordAuth

class AddPersonToSite(Method):
    """
    Adds the specified person to the specified site. If the person is
    already a member of the site, no errors are returned. Does not
    change the person's primary site.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        PasswordAuth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email']),
        Mixed(Site.fields['site_id'],
              Site.fields['login_base'])
        ]

    returns = Parameter(int, '1 if successful')
    event_type = 'AddTo'
    object_type = 'Site'
    object_ids = []

    def call(self, auth, person_id_or_email, site_id_or_login_base):
        # Get account information
        persons = Persons(self.api, [person_id_or_email])
        if not persons:
            raise PLCInvalidArgument, "No such account"

        person = persons.values()[0]

        # Get site information
        sites = Sites(self.api, [site_id_or_login_base])
        if not sites:
            raise PLCInvalidArgument, "No such site"

        site = sites.values()[0]

        if site['site_id'] not in person['site_ids']:
            site.add_person(person)
	self.object_ids = [site['site_id']]
	
        return 1
