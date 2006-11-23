#
# Thierry Parmentelat - INRIA
# 

import xmlrpclib

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.Peers import Peer, Peers
from PLC.Persons import Person, Persons

from PLC.Cache import Cache

class RefreshPeer(Method):
    """
    Query a peer PLC for its list of nodes, and refreshes
    the local database accordingly
    
    Returns a dict containing
    (*) 'plcname' :   the peer name
    (*) 'new_nodes' : the number of new nodes from that peer - may be negative
    (*) 'new_slices': the number of new slices from that peer - may be negative
    """
    
    roles = ['admin']
    
    accepts = [ Auth(),
		Parameter (int, "Peer id") ]
    
    returns = Parameter(dict, "plcname, new_nodes, new_slices")

    def call (self, auth, peer_id):
	
	### retrieve peer info
	peers = Peers (self.api,[peer_id])
        try:
            peer=peers[0]
        except:
            raise PLCInvalidArgument,'no such peer_id:%d'%peer_id
	
	### retrieve account info
	person_id = peer['person_id']
	persons = Persons (self.api,[person_id])
        try:
            person = persons[0]
        except:
            raise PLCInvalidArgument,'no such person_id:%d'%person_id
	
	## connect to the peer's API
        url=peer['peer_url']
	apiserver = xmlrpclib.ServerProxy (url,allow_none=True)

	### build up foreign auth
	auth={ 'Username': person['email'],
	       'AuthMethod' : 'password',
	       'AuthString' : person['password'],
	       'Role' : 'admin' }

	cache = Cache (self.api, peer, apiserver, auth)
	return cache.refresh_peer ()
