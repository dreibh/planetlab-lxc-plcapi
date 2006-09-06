from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Sites import Site, Sites
from PLC.Auth import PasswordAuth

class AdmRemovePersonFromSite(Method):
    """
    Removes the specified person from the specified site. If the
    person is not a member of the specified site, no error is
    returned.

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

        if site['site_id'] in person['site_ids']:
            person_id = person['person_id']
            site_id = site['site_id']
            self.api.db.do("DELETE FROM person_site" \
                           " WHERE person_id = %(person_id)d" \
                           " AND site_id = %(site_id)d",
                           locals())

        return 1
