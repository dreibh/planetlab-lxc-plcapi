from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.Slices import Slice, Slices
from PLC.Persons import Person, Persons
from PLC.Methods.GetSlices import GetSlices
from PLC.Methods.GetPersons import GetPersons

class SliceUsersList(GetSlices, GetPersons):
    """
    Deprecated. Can be implemented with GetSlices and GetPersons.

    List users that are members of the named slice.

    Users may only query slices of which they are members. PIs may
    query any of the slices at their sites. Admins may query any
    slice. If a slice that cannot be queried is specified details
    about that slice will not be returned.
    """

    status = "deprecated"

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        Slice.fields['name']
        ]

    returns = [Person.fields['email']]


    def call(self, auth, slice_name):

        slice_filter = [slice_name]
        slices = GetSlices.call(self, auth, slice_filter)
        if not slices:
            return []
        slice = slices[0]

        persons = GetPersons.call(self, auth, slice['person_ids'])
        person_emails = [person['email'] for person in persons]

        return person_emails
