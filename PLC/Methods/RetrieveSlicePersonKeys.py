from types import StringTypes

from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.Slices import Slice, Slices 
from PLC.Persons import Person, Persons
from PLC.Keys import Key, Keys

class RetrieveSlicePersonKeys(Method):
    """
    This method exposes the public ssh keys for people in a slice
    It expects a slice name or id, and returns a dictionary on emails.
    This method is designed to help third-party software authenticate
    users (e.g. the OMF Experiment Controller). 
    For this reason it is accessible with anonymous authentication.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'anonymous' ]

    applicable_fields = {
        'slice_id' : Slice.fields['slice_id'],
        'name' : Slice.fields['name'],
        }

    accepts = [
        Auth(),
        Mixed(Slice.fields['slice_id'],
              Slice.fields['name']),
        Filter(Person.fields),
        ]

    returns = Parameter (dict, " ssh keys hashed on emails")

    def call(self, auth, slice_id_or_name, person_filter=None):

        if person_filter is None: person_filter = {}

        # the people in the slice
        slice=Slices (self.api, slice_id_or_name, ['person_ids'])[0]
        slice_person_ids = slice['person_ids']
        
        # if caller has not specified person_id, use slice_person_ids
        if 'person_id' not in person_filter:
            person_filter['person_id']=slice_person_ids
        # otherwise, compute intersection
        else:
            caller_provided = person_filter['person_id']
            if not isinstance (caller_provided,list):
                caller_provided = [ caller_provided, ]
            person_filter['person_id'] = list ( set(caller_provided).intersection(slice_person_ids) )
        
        def merge (l1,l2): return l1+l2

        persons = Persons (self.api, person_filter, ['email','key_ids'] )
        key_id_to_email_hash = \
            dict ( reduce ( merge , [ [ (kid,p['email']) for kid in p['key_ids']] for p in persons ] ) ) 
        
        all_key_ids = reduce (merge, [ p['key_ids'] for p in persons ] )

        all_keys = Keys (self.api, all_key_ids)
        
        result={}
        for key in all_keys:
            key_id=key['key_id']
            email = key_id_to_email_hash[key_id]
            if email not in result: result[email]=[]
            result[email].append (key['key'])

        return  result
