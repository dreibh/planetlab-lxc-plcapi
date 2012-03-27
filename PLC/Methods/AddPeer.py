#
# Thierry Parmentelat - INRIA
#

from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth
from PLC.Peers import Peer, Peers

can_update = lambda (field, value): field in \
             ['peername', 'peer_url', 'key', 'cacert', 'shortname', 'hrn_root']

class AddPeer(Method):
    """
    Adds a new peer.

    Returns the new peer_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin']

    peer_fields = dict(filter(can_update, Peer.fields.items()))

    accepts = [
        Auth(),
        peer_fields
        ]

    returns = Parameter(int, "New peer_id (> 0) if successful")

    def call(self, auth, peer_fields):
        peer = Peer(self.api, peer_fields);
        peer.sync()
        self.event_objects = {'Peer': [peer['peer_id']]}

        return peer['peer_id']
