#
# Thierry Parmentelat - INRIA
# 

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.Peers import Peer, Peers
from PLC.Persons import Person, Persons

from PLC.Cache import Cache

class RefreshPeer(Method):
    """
    First queries a remote PLC for its name and updates the local peers table

    Then proceeds with fetching objects on the remote PLC, and updates the
    local database accordingly

    It requires the remote peer to be aware of our own name (as configured in PLC_NAME)

    Returns a dict containing
    (*) 'peername' :   the peer's name
    (*) 'new_xxx':     the number of new objects from that peer - may be negative
    (*) 'timers':      various stats on performance for optimization

    """
    
    roles = ['admin']
    
    accepts = [ Auth(),
                Mixed(Peer.fields['peer_id'],
                      Peer.fields['peername']),
                ]
    
    returns = {
        'new_sites': Parameter([dict], "List of new sites"),
        'new_keys': Parameter([dict], "List of new keys"),
        'new_nodes': Parameter([dict], "List of new nodes"),
        'new_persons': Parameter([dict], "List of new users"),
        'new_slice_attribute_types': Parameter([dict], "List of new slice attribute types"),
        'new_slices': Parameter([dict], "List of new slices"),
        'new_slice_attributes': Parameter([dict], "List of new slice attributes"),
        'timers': Parameter(dict, "(Debug) Timing information"),
        }

    def call (self, auth, peer_id_or_peername):
	peers = Peers(self.api, [peer_id_or_peername])
        if not peers:
            raise PLCInvalidArgument, "No such peer '%s'" % unicode(peer_id_or_peername)
        peer = peers[0]

	# Connect to peer API
        peer.connect()

        # Update peer name
        peername = peer.GetPeerName()
        if peer['peername'] != peername:
            peer['peername'] = peername
            peer.sync()

	cache = Cache(self.api, peer['peer_id'], peer)
        result = cache.refresh_peer()

        # Add peer name to result set
        result['peername'] = peername

        return result
