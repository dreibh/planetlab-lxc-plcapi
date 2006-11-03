from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.Peers import Peer, Peers

class GetPeers (Method):
    """
    returns information on known peers
    """

    roles = ['admin']

    accepts = [Auth(),
	       [Mixed(Peer.fields['peer_id'],
		      Peer.fields['peername'])],
	       ]

    returns = [Peer.fields]

    def call (self, auth, peer_id_or_peername_list = None):

	return Peers (self.api, peer_id_or_peername_list).values()
