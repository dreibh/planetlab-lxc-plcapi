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
    
    returns = Parameter(dict, 
                        'new_sites '
                        'new_keys '
                        'new_nodes '
                        'new_persons '
                        'new_slice_attribute_types '
                        'new_slices '
                        'new_slice_attributes '
                        'timers ')

    def call (self, auth, peer_id_or_peername):
	
	### retrieve peer info
	peers = Peers (self.api,[peer_id_or_peername])
        try:
            peer=peers[0]
        except:
            raise PLCInvalidArgument,'RefreshPeer: no such peer:%r'%peer_id_or_peername
	
	### retrieve account info
	auth_person_id = peer['auth_person_id']
	persons = Persons (self.api,[auth_person_id])
        try:
            person = persons[0]
        except:
            raise PLCInvalidArgument,'RefreshPeer: no such person_id:%d'%auth_person_id
	
	## connect to the peer's API
        url=peer['peer_url']
	apiserver = xmlrpclib.ServerProxy (url,allow_none=True)

	### build up foreign auth
	auth={ 'Username': person['email'],
	       'AuthMethod' : 'password',
	       'AuthString' : person['password'],
	       'Role' : 'admin' ,
               }

        # xxx
        # right now we *need* the remote peer to know our name
        # (this is used in the GetPeerData that we issue)
        # in general this will be true
        # however if anyone decides to change its own plc name things can get wrong
        # doing this should ensure things become right again after some iterations
        # that is, hopefully
        # might wish to change this policy once we have peer authentication, maybe
        
        # make sure we have the right name for that peer
        peername = apiserver.GetPeerName (auth)
        peer.update_name(peername)

        # we need a peer_id from there on
        peer_id = peer['peer_id']

        print 'Got peer_id',peer_id

	cache = Cache (self.api, peer_id, apiserver, auth)
        result = cache.refresh_peer ()
        result['peername']=peername

        return result
