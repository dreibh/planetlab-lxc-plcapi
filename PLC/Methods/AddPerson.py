from PLC.Faults import *
from PLC.Auth import Auth
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Table import Row
from PLC.Persons import Person, Persons
from PLC.TagTypes import TagTypes
from PLC.PersonTags import PersonTags, PersonTag

can_update = ['first_name', 'last_name', 'title',
              'email', 'password', 'phone', 'url', 'bio']

required=['email','first_name','last_name']

class AddPerson(Method):
    """
    Adds a new account. Any fields specified in person_fields are
    used, otherwise defaults are used.

    Accounts are disabled by default. To enable an account, use
    UpdatePerson().

    Returns the new person_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin', 'pi']

    accepted_fields = Row.accepted_fields(can_update,Person.fields)
    accepted_fields.update(Person.tags)

    accepts = [
        Auth(),
        accepted_fields
        ]

    returns = Parameter(int, 'New person_id (> 0) if successful')

    def call(self, auth, person_fields):

        # silently ignore 'enabled' if passed, for backward compat
        # this is forced to False below anyways
        if 'enabled' in person_fields: del person_fields['enabled']

        [native,tags,rejected]=Row.split_fields(person_fields,[Person.fields,Person.tags])

        # type checking
        native = Row.check_fields(native, self.accepted_fields)
        if rejected:
            raise PLCInvalidArgument, "Cannot add Person with column(s) %r"%rejected

        missing=[ r for r in required if r not in native ]
        if missing:
            raise PLCInvalidArgument, "Missing mandatory arguments %s to AddPerson"%missing

        # handle native fields
        native['enabled'] = False
        person = Person(self.api, native)
        person.sync()

        # handle tags
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
        self.message = 'Person %d added' % person['person_id']

        return person['person_id']
