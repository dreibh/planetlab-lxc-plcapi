from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.Persons import Person, Persons
from PLC.Sites import Site, Sites
from PLC.Slices import Slice, Slices
from PLC.Keys import Key, Keys

class GetSliceKeys(Method):
    """
    Returns an array of structs containing public key info for users in
    the specified slices. If slice_filter is specified and is an array
    of slice identifiers or slice names, or a struct of slice
    attributes, only slices matching the filter will be returned. If
    return_fields is specified, only the specified details will be
    returned.

    Users may only query slices of which they are members. PIs may
    query any of the slices at their sites. Admins and nodes may query
    any slice. If a slice that cannot be queried is specified in
    slice_filter, details about that slice will not be returned.
    """

    roles = ['admin', 'pi', 'user', 'node']

    accepts = [
        Auth(),
        Mixed([Mixed(Slice.fields['slice_id'],
                     Slice.fields['name'])],
              Filter(Slice.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [
        {
        'slice_id': Slice.fields['slice_id'],
        'name': Slice.fields['name'],
        'person_id': Person.fields['person_id'],
        'email': Person.fields['email'],
        'key': Key.fields['key']
        }]

    def call(self, auth, slice_filter = None, return_fields = None):
        slice_fields = ['slice_id', 'name']
        person_fields = ['person_id', 'email']
        key_fields = ['key']

        # If we are not admin, make sure to return only viewable
        # slices.
        if isinstance(self.caller, Person) and \
           'admin' not in self.caller['roles']:
            # Get slices that we are able to view
            valid_slice_ids = self.caller['slice_ids']
            if 'pi' in self.caller['roles'] and self.caller['site_ids']:
                sites = Sites(self.api, self.caller['site_ids'])
                for site in sites:
                    valid_slice_ids += site['slice_ids']

            if not valid_slice_ids:
                return []

            if slice_filter is None:
                slice_filter = valid_slice_ids

        if return_fields:
            slice_return_fields = filter(lambda field: field in slice_fields, return_fields)
            person_return_fields = filter(lambda field: field in person_fields, return_fields)
            key_return_fields = filter(lambda field: field in key_fields, return_fields)
        else:
            slice_return_fields = slice_fields
            person_return_fields = person_fields
            key_return_fields = key_fields

        # Must query at least Slice.slice_id, Slice.person_ids,
        # and Person.person_id and Person.key_ids so we can join data correctly
        slice_added_fields = set(['slice_id', 'person_ids']).difference(slice_return_fields)
        slice_return_fields += slice_added_fields
        person_added_fields = set(['person_id', 'key_ids']).difference(person_return_fields)
        person_return_fields += person_added_fields
        key_added_fields = set(['key_id']).difference(key_return_fields)
        key_return_fields += key_added_fields

        # Get the slices
        all_slices = Slices(self.api, slice_filter, slice_return_fields).dict('slice_id')
        slice_ids = all_slices.keys()
        slices = all_slices.values()

        # Filter out slices that are not viewable
        if isinstance(self.caller, Person) and \
           'admin' not in self.caller['roles']:
            slices = filter(lambda slice: slice['slice_id'] in valid_slice_ids, slices)

        # Get the persons
        person_ids = set()
        for slice in slices:
            person_ids.update(slice['person_ids'])

        all_persons = Persons(self.api, list(person_ids), person_return_fields).dict('person_id')
        person_ids = all_persons.keys()
        persons = all_persons.values()

        # Get the keys
        key_ids = set()
        for person in persons:
            key_ids.update(person['key_ids'])

        all_keys = Keys(self.api, list(key_ids), key_return_fields).dict('key_id')
        key_ids = all_keys.keys()
        keys = all_keys.values()

        # Create slice_keys list
        slice_keys = []
        slice_fields = list(set(slice_return_fields).difference(slice_added_fields))
        person_fields = list(set(person_return_fields).difference(person_added_fields))
        key_fields = list(set(key_return_fields).difference(key_added_fields))

        for slice in slices:
            slice_key = dict.fromkeys(slice_fields + person_fields + key_fields)
            if not slice['person_ids']:
                continue
            for person_id in slice['person_ids']:
                person = all_persons[person_id]
                if not person['key_ids']:
                    continue
                for key_id in person['key_ids']:
                    key = all_keys[key_id]
                    slice_key.update(dict(filter(lambda (k, v): k in slice_fields, slice.items())))
                    slice_key.update(dict(filter(lambda (k, v): k in person_fields, person.items())))
                    slice_key.update(dict(filter(lambda (k, v): k in key_fields, key.items())))
                    slice_keys.append(slice_key.copy())

        return slice_keys
