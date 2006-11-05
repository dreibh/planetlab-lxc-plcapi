#
# Thierry Parmentelat - INRIA
# 

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.Peers import Peer, Peers

can_update = lambda(k,v): k in ['peername','peer_url','person_id']

class AddPeer (Method):
    """
    Creates a peer entry in the database and returns its id
    Temporarily, requires to provide a person_id 
    this is used to store the credentials that we'll
    use when connecting to the peer's API
    """

    roles = ['admin']
    peer_fields = dict( [x for x in Peer.fields.iteritems() if can_update(x)] )

    accepts = [ Auth(),
		peer_fields
		]

    returns = Parameter (int, "peer_id")

    def call (self, auth, fields):

	peer = Peer (self.api,fields);
	peer.sync()
	
	return peer['peer_id']
	

