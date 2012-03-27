import time

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Slices import Slice, Slices
from PLC.Auth import Auth
from PLC.GPG import gpg_sign, gpg_verify
from PLC.InitScripts import InitScript, InitScripts

from PLC.Methods.GetSlivers import get_slivers

class GetSliceTicket(Method):
    """
    Returns a ticket for, or signed representation of, the specified
    slice. Slice tickets may be used to manually instantiate or update
    a slice on a node. Present this ticket to the local Node Manager
    interface to redeem it.

    If the slice has not been added to a node with AddSliceToNodes,
    and the ticket is redeemed on that node, it will be deleted the
    next time the Node Manager contacts the API.

    Users may only obtain tickets for slices of which they are
    members. PIs may obtain tickets for any of the slices at their
    sites, or any slices of which they are members. Admins may obtain
    tickets for any slice.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin', 'pi', 'user', 'peer']

    accepts = [
        Auth(),
        Mixed(Slice.fields['slice_id'],
              Slice.fields['name']),
        ]

    returns = Parameter(str, 'Signed slice ticket')

    def call(self, auth, slice_id_or_name):
        slices = Slices(self.api, [slice_id_or_name])
        if not slices:
            raise PLCInvalidArgument, "No such slice"
        slice = slices[0]

        # Allow peers to obtain tickets for their own slices
        if slice['peer_id'] is not None:
            if not isinstance(self.caller, Peer):
                raise PLCInvalidArgument, "Not a local slice"
            elif slice['peer_id'] != self.caller['peer_id']:
                raise PLCInvalidArgument, "Only the authoritative peer may obtain tickets for that slice"

        # Tickets are the canonicalized XML-RPC methodResponse
        # representation of a partial GetSlivers() response, i.e.,

        initscripts = InitScripts(self.api, {'enabled': True})

        data = {
            'timestamp': int(time.time()),
            'initscripts': initscripts,
            'slivers': get_slivers(self.api, self.caller, auth, [slice['slice_id']]),
            }

        # Sign ticket
        signed_ticket = gpg_sign((data,),
                                 self.api.config.PLC_ROOT_GPG_KEY,
                                 self.api.config.PLC_ROOT_GPG_KEY_PUB,
                                 methodresponse = True,
                                 detach_sign = False)

        # Verify ticket
        gpg_verify(signed_ticket,
                   self.api.config.PLC_ROOT_GPG_KEY_PUB)

        return signed_ticket
