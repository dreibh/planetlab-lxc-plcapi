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
from PLC.Slices import Slice, Slices
from PLC.SliceTags import SliceTags

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
        node_fields = [ field for field in Node.fields if field \
                            not in ['boot_nonce', 'key', 'session', 'root_person_ids']]
        node_fields += ['hrn']
        nodes = Nodes(self.api, {'peer_id': None}, node_fields);
        # filter out whitelisted nodes
        nodes = [ n for n in nodes if not n['slice_ids_whitelist']]


        person_fields = [ field for field in Person.fields if field \
                              not in ['password', 'verification_key', 'verification_expires']]

        site_fields = Site.fields
        slice_fields = Slice.fields
        try:
            person_fields += ['sfa_created','hrn']
            site_fields += ['sfa_created','hrn']
            slice_fields +=['sfa_created','hrn']
        
            # XXX Optimize to return only those Persons, Keys, and Slices
            # necessary for slice creation on the calling peer's nodes.

            # filter out special person
        
            persons = Persons(self.api, {'~email':[self.api.config.PLC_API_MAINTENANCE_USER, self.api.config.PLC_ROOT_USER], 'peer_id': None}, person_fields)

            # filter out system slices
            system_slice_ids = SliceTags(self.api, {'name': 'system', 'value': '1'}).dict('slice_id')
            slices = Slices(self.api, {'peer_id': None,'~slice_id':system_slice_ids.keys()}, slice_fields)

            sites = Sites(self.api, {'peer_id': None}, site_fields)
       
            # filter out objects with  sfa_created=True
            filtered_sites = [site for site in sites if site.get('sfa_created', None) != 'True']
            filtered_slices = [slice for slice in slices if slice.get('sfa_created', None) != 'True']
            filtered_persons = [person for person in persons if person.get('sfa_created', None) != 'True']  

        except:
            # handle peers with old version of MyPLC that does not support 'sfa_created' and 'hrn' fields for Site/Slice/Person 
 
            # XXX Optimize to return only those Persons, Keys, and Slices
            # necessary for slice creation on the calling peer's nodes.

            # filter out special person

            filtered_persons = Persons(self.api, {'~email':[self.api.config.PLC_API_MAINTENANCE_USER, self.api.config.PLC_ROOT_USER], 'peer_id': None}, person_fields)

            # filter out system slices
            system_slice_ids = SliceTags(self.api, {'name': 'system', 'value': '1'}).dict('slice_id')
            filtered_slices = Slices(self.api, {'peer_id': None,
                                   '~slice_id':system_slice_ids.keys()}, slice_fields)

            filtered_sites = Sites(self.api, {'peer_id': None}, site_fields)


        result = {
            'Sites': filtered_sites,
            'Keys': Keys(self.api, {'peer_id': None}),
            'Nodes': nodes,
            'Persons': filtered_persons,
            'Slices': filtered_slices,
            }


        if isinstance(self.caller, Peer):
            result['PeerNodes'] = Nodes(self.api, {'peer_id': self.caller['peer_id']})

        result['db_time'] = time.time() - start

        return result
