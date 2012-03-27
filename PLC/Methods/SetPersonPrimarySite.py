from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Person, Persons
from PLC.Sites import Site, Sites
from PLC.Auth import Auth

class SetPersonPrimarySite(Method):
    """
    Makes the specified site the person's primary site. The person
    must already be a member of the site.

    Admins may update anyone. All others may only update themselves.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        Auth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email']),
        Mixed(Site.fields['site_id'],
              Site.fields['login_base'])
        ]

    returns = Parameter(int, '1 if successful')

    object_type = 'Person'

    def call(self, auth, person_id_or_email, site_id_or_login_base):
        # Get account information
        persons = Persons(self.api, [person_id_or_email])
        if not persons:
            raise PLCInvalidArgument, "No such account"
        person = persons[0]

        if person['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local account"

        # Authenticated function
        assert self.caller is not None

        # Non-admins can only update their own primary site
        if 'admin' not in self.caller['roles'] and \
           self.caller['person_id'] != person['person_id']:
            raise PLCPermissionDenied, "Not allowed to update specified account"

        # Get site information
        sites = Sites(self.api, [site_id_or_login_base])
        if not sites:
            raise PLCInvalidArgument, "No such site"
        site = sites[0]

        if site['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local site"

        if site['site_id'] not in person['site_ids']:
            raise PLCInvalidArgument, "Not a member of the specified site"

        person.set_primary_site(site)

        return 1
