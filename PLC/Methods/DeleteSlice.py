from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Slices import Slice, Slices
from PLC.Auth import Auth

class DeleteSlice(Method):
    """
    Deletes the specified slice.

    Users may only delete slices of which they are members. PIs may
    delete any of the slices at their sites, or any slices of which
    they are members. Admins may delete any slice.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        Mixed(Slice.fields['slice_id'],
              Slice.fields['name']),
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, slice_id_or_name):
        slices = Slices(self.api, [slice_id_or_name])
        if not slices:
            raise PLCInvalidArgument, "No such slice"
        slice = slices[0]

        if slice['peer_id'] is not None:
            raise PLCInvalidArgument, "Not a local slice"

        if 'admin' not in self.caller['roles']:
            if self.caller['person_id'] in slice['person_ids']:
                pass
            elif 'pi' not in self.caller['roles']:
                raise PLCPermissionDenied, "Not a member of the specified slice"
            elif slice['site_id'] not in self.caller['site_ids']:
                raise PLCPermissionDenied, "Specified slice not associated with any of your sites"

        slice.delete()
        self.event_objects = {'Slice': [slice['slice_id']]}

        return 1
