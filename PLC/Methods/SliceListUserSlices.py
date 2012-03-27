from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.Slices import Slice, Slices
from PLC.Persons import Person, Persons
from PLC.Methods.GetSlices import GetSlices
from PLC.Methods.GetPersons import GetPersons

class SliceListUserSlices(GetSlices, GetPersons):
    """
    Deprecated. Can be implemented with GetPersons and GetSlices.

    Return the slices the specified user (by email address) is a member of.

    Users may only query slices of which they are members. PIs may
    query any of the slices at their sites. Admins may query any
    slice. If a slice that cannot be queried is specified in
    slice_filter, details about that slice will not be returned.
    """

    status = "deprecated"

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        Person.fields['email']
        ]

    returns = [Slice.fields['name']]


    def call(self, auth, email):

        persons = GetPersons.call(self, auth, [email])
        if not persons:
            return []
        person = persons[0]
        slice_ids = person['slice_ids']
        if not slice_ids:
            return []

        slices = GetSlices.call(self, auth, slice_ids)
        slice_names = [slice['name'] for slice in slices]

        return slice_names
