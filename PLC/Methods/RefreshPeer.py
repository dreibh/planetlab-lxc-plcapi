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
##from PLC.ForeignNodes import ForeignNode, ForeignNodes


class RefreshPeer(Method):
    """
    Query a peer PLC for its list of nodes, and refreshes
    the local database accordingly
    
    Returns a tuple containing
    (*) the peer name
    (*) the number of new nodes from that peer - may be negative
    (*) the number of new slices from that peer - may be negative
    """
    
    roles = ['admin']
    
    accepts = [ Auth(),
		Parameter (int, "Peer id") ]
    
    returns = Parameter(int, "Delta in number of foreign nodes attached to that peer")

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
	
	### build up foreign auth
	auth={ 'Username': person['email'],
	       'AuthMethod' : 'password',
	       'AuthString' : person['password'],
	       'Role' : 'admin' }

	## connect to the peer's API
        url=peer['peer_url']
        print 'url=',url
	apiserver = xmlrpclib.Server (url)
	print 'auth=',auth

	peer_get_nodes = apiserver.GetNodes(auth)
        nb_new_nodes = peer.refresh_nodes(peer_get_nodes)
        
        peer_get_slices = apiserver.GetSlices(auth)
        nb_new_slices = peer.refresh_slices(peer_get_slices)
        
	return (self.api.config.PLC_NAME,nb_new_nodes,nb_new_slices)
