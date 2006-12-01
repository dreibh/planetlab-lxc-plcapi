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

    roles = ['admin']

    accepts = [Auth(),
               Parameter (int, "Peer id"),
               ]
    # for RefreshPeer 
    returns = Parameter (dict,"Sites, Keys, Nodes, Persons, Slices")

    def call (self, auth, peer_id):
        # xxx a peer cannot yet compute it's peer_id under another plc
        # so we return all foreign objects by now
        
        t_start = time.time()
        result = {
            'Sites-local' : Sites (self.api,{'peer_id':None}),
            'Sites-peer' : Sites (self.api,{'~peer_id':None}),
            'Keys-local' : Keys (self.api,{'peer_id':None}),
            'Keys-peer' : Keys (self.api,{'~peer_id':None}),
            'Nodes-local' : Nodes (self.api,{'peer_id':None}),
            'Nodes-peer' : Nodes (self.api,{'~peer_id':None}),
            'Persons-local' : Persons (self.api,{'peer_id':None}),
            'Persons-peer' : Persons (self.api,{'~peer_id':None}),
            'SliceAttibuteTypes-local' : SliceAttributeTypes (self.api,{'peer_id':None}),
            'SliceAttibuteTypes-peer' : SliceAttributeTypes (self.api,{'~peer_id':None}),
            'Slices-local' : Slices (self.api,{'peer_id':None}),
            'Slices-peer' : Slices (self.api,{'~peer_id':None}),
            'SliceAttributes-local': SliceAttributes (self.api,{'peer_id':None}),
            'SliceAttributes-peer': SliceAttributes (self.api,{'~peer_id':None}),
            }
        t_end = time.time()
        result['ellapsed'] = t_end-t_start
        return result
        
