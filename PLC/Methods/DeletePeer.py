from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth
from PLC.Peers import Peer, Peers

class DeletePeer(Method):
    """
    Mark an existing peer as deleted. All entities (e.g., slices,
    keys, nodes, etc.) for which this peer is authoritative will also
    be deleted or marked as deleted.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Mixed(Peer.fields['peer_id'],
              Peer.fields['peername'])
        ]

    returns = Parameter(int, "1 if successful")

    def call(self, auth, peer_id_or_name):
        # Get account information
        peers = Peers(self.api, [peer_id_or_name])
        if not peers:
            raise PLCInvalidArgument, "No such peer"

        peer = peers[0]
        peer.delete()

        # Log affected objects
        self.event_objects = {'Peer': [peer['peer_id']]}

        return 1
