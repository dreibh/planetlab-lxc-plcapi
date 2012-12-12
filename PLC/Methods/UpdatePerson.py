from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth
from PLC.Table import Row
from PLC.Persons import Person, Persons
from PLC.sendmail import sendmail
from PLC.TagTypes import TagTypes
from PLC.PersonTags import PersonTags, PersonTag

related_fields = Person.related_fields.keys()
can_update = ['first_name', 'last_name', 'title', 'email',
              'password', 'phone', 'url', 'bio', 'accepted_aup',
              'enabled'] + related_fields

class UpdatePerson(Method):
    """
    Updates a person. Only the fields specified in person_fields are
    updated, all other fields are left untouched.

    Users and techs can only update themselves. PIs can only update
    themselves and other non-PIs at their sites.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepted_fields = Row.accepted_fields(can_update,Person.fields)
    # xxx check the related_fields feature
    accepted_fields.update(Person.related_fields)
    accepted_fields.update(Person.tags)

    accepts = [
        Auth(),
        Mixed(Person.fields['person_id'],
              Person.fields['email']),
        accepted_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, person_id_or_email, person_fields):
        # split provided fields
        [native,related,tags,rejected] = Row.split_fields(person_fields,[Person.fields,Person.related_fields,Person.tags])

        # type checking
        native = Row.check_fields (native, self.accepted_fields)
        if rejected:
            raise PLCInvalidArgument, "Cannot update Person column(s) %r"%rejected

        # Authenticated function
        assert self.caller is not None

        # Get account information
        persons = Persons(self.api, [person_id_or_email])
        if not persons:
            raise PLCInvalidArgument, "No such account %s"%person_id_or_email
        person = persons[0]

        if person['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local account %s"%person_id_or_email

        # Check if we can update this account
        if not self.caller.can_update(person):
            raise PLCPermissionDenied, "Not allowed to update specified account"

        # Make requested associations
        for k,v in related.iteritems():
            person.associate (auth, k, v)

        person.update(native)
        person.update_last_updated(False)
        person.sync(commit=True)
        
        # send a mail
        if 'enabled' in person_fields:
            To = [("%s %s" % (person['first_name'], person['last_name']), person['email'])]
            Cc = []
            if person['enabled']:
                Subject = "%s account enabled" % (self.api.config.PLC_NAME)
                Body = "Your %s account has been enabled. Please visit %s to access your account." % (self.api.config.PLC_NAME, self.api.config.PLC_WWW_HOST)
            else:
                Subject = "%s account disabled" % (self.api.config.PLC_NAME)
                Body = "Your %s account has been disabled. Please contact your PI or PlanetLab support for more information" % (self.api.config.PLC_NAME)
            sendmail(self.api, To = To, Cc = Cc, Subject = Subject, Body = Body)


        for (tagname,value) in tags.iteritems():
            # the tagtype instance is assumed to exist, just check that
            tag_types = TagTypes(self.api,{'tagname':tagname})
            if not tag_types:
                raise PLCInvalidArgument,"No such TagType %s"%tagname
            tag_type = tag_types[0]
            person_tags=PersonTags(self.api,{'tagname':tagname,'person_id':person['person_id']})
            if not person_tags:
                person_tag = PersonTag(self.api)
                person_tag['person_id'] = person['person_id']
                person_tag['tag_type_id'] = tag_type['tag_type_id']
                person_tag['tagname']  = tagname
                person_tag['value'] = value
                person_tag.sync()
            else:
                person_tag = person_tags[0]
                person_tag['value'] = value
                person_tag.sync()

        # Logging variables
        self.event_objects = {'Person': [person['person_id']]}

        # Redact password
        if 'password' in person_fields:
            person_fields['password'] = "Removed by API"
        self.message = 'Person %d updated: %s.' % \
                       (person['person_id'], person_fields.keys())
        if 'enabled' in person_fields:
            self.message += ' Person enabled'

        return 1
