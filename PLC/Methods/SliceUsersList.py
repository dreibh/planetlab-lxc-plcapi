from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.Slices import Slice, Slices
from PLC.Persons import Person, Persons

class SliceUsersList(Method):
    """
    Deprecated. Can be implemented with GetSlices.

    List users that are members of the named slice.

    Users may only query slices of which they are members. PIs may
    query any of the slices at their sites. Admins may query any
    slice. If a slice that cannot be queried is specified details 
    about that slice will not be returned.
    """

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        Slice.fields['name']
	]

    returns = [Person.fields['email']]
    

    def call(self, auth, slice_name):
	# If we are not admin, make sure to return only viewable
	# slices.
	slice_filter = [slice_name]
        slices = Slices(self.api, slice_filter)
	if not slices:
            raise PLCInvalidArgument, "No such slice"
	slice = slices[0]
     
	if 'admin' not in self.caller['roles']:
            # Get slices that we are able to view
            valid_slice_ids = self.caller['slice_ids']
            if 'pi' in self.caller['roles'] and self.caller['site_ids']:
                sites = Sites(self.api, self.caller['site_ids'])
                for site in sites:
                    valid_slice_ids += site['slice_ids']

            if not valid_slice_ids:
                return []

	    if slice['slice_id'] not in valid_slice_ids:
		return []
	
	persons = Persons(self.api, slice['person_ids'])
	person_names = [person['email'] for person in persons]

        return person_names
