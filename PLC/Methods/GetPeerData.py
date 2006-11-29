#
# Thierry Parmentelat - INRIA
# 

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
        # so we return evrything by now
        
        return {
            'Sites' : Sites (self.api),
            'Keys' : Keys (self.api),
            'Nodes' : Nodes (self.api),
            'Persons' : Persons (self.api),
            'SliceAttibuteTypes' : SliceAttributeTypes (self.api),
            'Slices' : Slices (self.api),
            'SliceAttributes': SliceAttributes (self.api)
            }
        
