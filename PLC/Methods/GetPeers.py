#
# Thierry Parmentelat - INRIA
# 

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth

from PLC.Peers import Peer, Peers

class GetPeers (Method):
    """
    Returns an array of structs containing details about peers. If
    person_filter is specified and is an array of peer identifiers or
    peer names, or a struct of peer attributes, only peers matching
    the filter will be returned. If return_fields is specified, only the
    specified details will be returned.
    """

    roles = ['admin', 'node']

    accepts = [
        Auth(),
        Mixed([Mixed(Peer.fields['peer_id'],
                     Peer.fields['peername'])],
              Filter(Peer.fields)),
        Parameter([str], "List of fields to return", nullok = True)        
        ]

    returns = [Peer.fields]

    def call (self, auth, peer_filter = None, return_fields = None):
	return Peers(self.api, peer_filter, return_fields)
