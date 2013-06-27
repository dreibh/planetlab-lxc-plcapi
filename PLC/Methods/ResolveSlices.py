from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.Slices import Slice, Slices

class ResolveSlices(Method):
    """
    This method is similar to GetSlices, except that (1) the returned
    columns are restricted to 'name', 'slice_id' and 'expires', and
    (2) it returns expired slices too. This method is designed to help
    third-party software solve slice names from their slice_id
    (e.g. PlanetFlow Central). For this reason it is accessible with
    anonymous authentication (among others).
    """

    roles = ['admin', 'pi', 'user', 'tech', 'anonymous' ]

    applicable_fields = {
        'slice_id' : Slice.fields['slice_id'],
        'name' : Slice.fields['name'],
        'expires': Slice.fields['expires'],
        }

    accepts = [
        Auth(),
        Mixed([Mixed(Slice.fields['slice_id'],
                     Slice.fields['name'])],
              Parameter(str,"name"),
              Parameter(int,"slice_id"),
              Filter(applicable_fields))
        ]

    returns = [applicable_fields]

    def call(self, auth, slice_filter = None):

        # Must query at least slice_id (see below)
        return_fields = self.applicable_fields.keys()
        # pass expires=0
        slices = Slices(self.api, slice_filter, return_fields, 0)
        return slices
