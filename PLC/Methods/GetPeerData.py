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
from PLC.SliceAttributes import SliceAttribute, SliceAttributes
from PLC.Slices import Slice, Slices

class GetPeerData(Method):
    """
    Returns lists of local objects that a peer should cache in its
    database as foreign objects. Also returns the list of foreign
    nodes in this database, for which the calling peer is
    authoritative, to assist in synchronization of slivers.
    
    See the implementation of RefreshPeer for how this data is used.
    """

    roles = ['admin', 'peer']

    accepts = [Auth()]

    returns = {
        'Sites': Parameter([dict], "List of local sites"),
        'Keys': Parameter([dict], "List of local keys"),
        'Nodes': Parameter([dict], "List of local nodes"),
        'Persons': Parameter([dict], "List of local users"),
        'Slices': Parameter([dict], "List of local slices"),
        'db_time': Parameter(float, "(Debug) Database fetch time"),
        }

    def call (self, auth):
        start = time.time()

        # Filter out various secrets
        node_fields = filter(lambda field: field not in \
                             ['boot_nonce', 'key', 'session', 'root_person_ids'],
                             Node.fields)

        person_fields = filter(lambda field: field not in \
                               ['password', 'verification_key', 'verification_expires'],
                               Person.fields)

        # XXX Optimize to return only those Persons, Keys, and Slices
        # necessary for slice creation on the calling peer's nodes.
        result = {
            'Sites': Sites(self.api, {'peer_id': None}),
            'Keys': Keys(self.api, {'peer_id': None}),
            'Nodes': Nodes(self.api, {'peer_id': None}, node_fields),
            'Persons': Persons(self.api, {'peer_id': None}, person_fields),
            'Slices': Slices(self.api, {'peer_id': None}),
            }

        if isinstance(self.caller, Peer):
            result['PeerNodes'] = Nodes(self.api, {'peer_id': self.caller['peer_id']})

        result['db_time'] = time.time() - start

        return result
