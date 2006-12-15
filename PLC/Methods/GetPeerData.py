#
# Thierry Parmentelat - INRIA
# 

import time

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.Peers import Peer, Peers

from PLC.Sites import Site, Sites
from PLC.Keys import Key, Keys
from PLC.Nodes import Node, Nodes
from PLC.Persons import Person, Persons
from PLC.SliceAttributeTypes import SliceAttributeType, SliceAttributeTypes
from PLC.Slices import Slice, Slices
from PLC.SliceAttributes import SliceAttribute, SliceAttributes

class GetPeerData (Method):
    """
    Gather all data needed by RefreshPeer in a single xmlrpc request

    Expects a peer id or peer name, that identifies the requesting peer
    
    Returns a dict containing, for the various types of cached entities,
    the local objects as well as the ones attached to that peer
    """

    roles = ['admin', 'peer']

    accepts = [
        Auth(),
        Mixed(Peer.fields['peer_id'],
              Peer.fields['peername']),
        ]

    # for RefreshPeer 
    returns = {
        'Sites-local': Parameter([dict], "List of local sites"),
        'Sites-peer': Parameter([dict], "List of foreign sites"),
        'Keys-local': Parameter([dict], "List of local keys"),
        'Keys-peer':  Parameter([dict], "List of foreign keys"),
        'Nodes-local':  Parameter([dict], "List of local nodes"),
        'Nodes-peer':  Parameter([dict], "List of foreign nodes"),
        'Persons-local':  Parameter([dict], "List of local users"),
        'Persons-peer':  Parameter([dict], "List of foreign users"),
        'SliceAttibuteTypes-local':  Parameter([dict], "List of local slice attribute types"),
        'SliceAttibuteTypes-peer':  Parameter([dict], "List of foreign slice attribute types"),
        'Slices-local':  Parameter([dict], "List of local slices"),
        'Slices-peer':  Parameter([dict], "List of foreign slices"),
        'SliceAttributes-local':  Parameter([dict], "List of local slice attributes"),
        'SliceAttributes-peer':  Parameter([dict], "List of foreign slice attributes"),
        }

    def call (self, auth, peer_id_or_peername):

        # checking the argument
        try:
            peer_id = Peers(self.api,[peer_id_or_peername])[0]['peer_id']
        except:
            raise PLCInvalidArgument,'GetPeerData: no such peer %r'%peer_id_or_peername
        
        t_start = time.time()
        result = {
            'Sites-local' : Sites (self.api,{'peer_id':None}),
            'Sites-peer' : Sites (self.api,{'peer_id':peer_id}),
            'Keys-local' : Keys (self.api,{'peer_id':None}),
            'Keys-peer' : Keys (self.api,{'peer_id':peer_id}),
            'Nodes-local' : Nodes (self.api,{'peer_id':None}),
            'Nodes-peer' : Nodes (self.api,{'peer_id':peer_id}),
            'Persons-local' : Persons (self.api,{'peer_id':None}),
            'Persons-peer' : Persons (self.api,{'peer_id':peer_id}),
            'SliceAttibuteTypes-local' : SliceAttributeTypes (self.api,{'peer_id':None}),
            'SliceAttibuteTypes-peer' : SliceAttributeTypes (self.api,{'peer_id':peer_id}),
            'Slices-local' : Slices (self.api,{'peer_id':None}),
            'Slices-peer' : Slices (self.api,{'peer_id':peer_id}),
            'SliceAttributes-local': SliceAttributes (self.api,{'peer_id':None}),
            'SliceAttributes-peer': SliceAttributes (self.api,{'peer_id':peer_id}),
            }
        t_end = time.time()
        result['ellapsed'] = t_end-t_start
        return result
        
