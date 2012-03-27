from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth
from PLC.Peers import Peer, Peers

can_update = lambda (field, value): field in \
             ['peername', 'peer_url', 'key', 'cacert', 'shortname', 'hrn_root']

class UpdatePeer(Method):
    """
    Updates a peer. Only the fields specified in peer_fields are
    updated, all other fields are left untouched.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    peer_fields = dict(filter(can_update, Peer.fields.items()))

    accepts = [
        Auth(),
        Mixed(Peer.fields['peer_id'],
              Peer.fields['peername']),
        peer_fields
        ]

    returns = Parameter(int, "1 if successful")

    def call(self, auth, peer_id_or_name, peer_fields):
        peer_fields = dict(filter(can_update, peer_fields.items()))

        # Get account information
        peers = Peers(self.api, [peer_id_or_name])
        if not peers:
            raise PLCInvalidArgument, "No such peer"
        peer = peers[0]

        if isinstance(self.caller, Peer):
            if self.caller['peer_id'] != peer['peer_id']:
                raise PLCPermissionDenied, "Not allowed to update specified peer"

        peer.update(peer_fields)
        peer.sync()

        # Log affected objects
        self.event_objects = {'Peer': [peer['peer_id']]}

        return 1
