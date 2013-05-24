from PLC.Faults import *
from PLC.Auth import Auth
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Sites import Site, Sites
from PLC.Persons import Person, Persons
from PLC.PersonTags import PersonTags, PersonTag
from PLC.Namespace import email_to_hrn
from PLC.TagTypes import TagTypes

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

        # maintain person's hrn
        # only if at this point we have a single site 
        # which means, there was no site attached to person upon entering this call
        try:
            had_no_site= (len (person['site_ids']) == 0)
            if had_no_site: 
                login_base=site['login_base']
                root_auth = self.api.config.PLC_HRN_ROOT
                hrn=email_to_hrn("%s.%s"%(root_auth,login_base),person['email'])
                tagname='hrn'
                tag_type = TagTypes(self.api,{'tagname':tagname})[0]
                person_tags=PersonTags(self.api,{'tagname':tagname,'person_id':person['person_id']})
                if not person_tags:
                    person_tag = PersonTag(self.api)
                    person_tag['person_id'] = person['person_id']
                    person_tag['tag_type_id'] = tag_type['tag_type_id']
                    person_tag['tagname']  = tagname
                    person_tag['value'] = hrn
                    person_tag.sync()
                else:
                    person_tag = person_tags[0]
                    person_tag['value'] = value
                    person_tag.sync() 
        except Exception,e:
            print "BEG Warning, cannot maintain person's hrn, %s"%e
            import traceback
            traceback.print_exc()
            print "END Warning, cannot maintain person's hrn, %s"%e
                

        return 1
