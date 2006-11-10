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
from PLC.ForeignNodes import ForeignNode, ForeignNodes


class RefreshPeer(Method):
    """
    Query a peer PLC for its list of nodes, and refreshes
    the local database accordingly
    
    Returns the number of new nodes from that peer - may be negative
    """
    
    roles = ['admin']
    
    accepts = [ Auth(),
		Parameter (int, "Peer id") ]
    
    returns = Parameter(int, "Delta in number of foreign nodes attached to that peer")

    def call (self, auth, peer_id):
	
	### retrieve peer info
	peers = Peers (self.api,[peer_id])
        if not peers:
            raise PLCInvalidArgument,'no such peer_id:%d'%peer_id
        peer=peers[0]
	
	### retrieve account info
	person_id = peer['person_id']
	persons = Persons (self.api,[person_id])
        if not persons:
            raise PLCInvalidArgument,'no such person_id:%d'%person_id
	person = persons[0]
	
	### build up foreign auth
	auth={ 'Username': person['email'],
	       'AuthMethod' : 'password',
	       'AuthString' : person['password'],
	       'Role' : 'admin' }

	## connect to the peer's API
        url=peer['peer_url']+"/PLCAPI/"
        print 'url=',url
	apiserver = xmlrpclib.Server (url)
	print 'auth=',auth
	current_peer_nodes = apiserver.GetNodes(auth)
        print 'current_peer_nodes',current_peer_nodes

	## manual feed for tests
        n11={'session': None, 'slice_ids': [], 'nodegroup_ids': [], 'last_updated': 1162884349, 'version': None, 'nodenetwork_ids': [], 'boot_state': 'inst', 'hostname': 'n11.plc1.org', 'site_id': 1, 'ports': None, 'pcu_ids': [], 'boot_nonce': None, 'node_id': 1, 'root_person_ids': [], 'key': None, 'date_created': 1162884349, 'model': None, 'conf_file_ids': [], 'ssh_rsa_key': None}
        n12={'session': None, 'slice_ids': [], 'nodegroup_ids': [], 'last_updated': 1162884349, 'version': None, 'nodenetwork_ids': [], 'boot_state': 'inst', 'hostname': 'n12.plc1.org', 'site_id': 1, 'ports': None, 'pcu_ids': [], 'boot_nonce': None, 'node_id': 1, 'root_person_ids': [], 'key': None, 'date_created': 1162884349, 'model': None, 'conf_file_ids': [], 'ssh_rsa_key': None}
        n21={'session': None, 'slice_ids': [], 'nodegroup_ids': [], 'last_updated': 1162884349, 'version': None, 'nodenetwork_ids': [], 'boot_state': 'boot', 'hostname': 'n21.plc2.org', 'site_id': 1, 'ports': None, 'pcu_ids': [], 'boot_nonce': None, 'node_id': 1, 'root_person_ids': [], 'key': None, 'date_created': 1162884349, 'model': None, 'conf_file_ids': [], 'ssh_rsa_key': None}
        n22={'session': None, 'slice_ids': [], 'nodegroup_ids': [], 'last_updated': 1162884349, 'version': None, 'nodenetwork_ids': [], 'boot_state': 'boot', 'hostname': 'n22.plc2.org', 'site_id': 1, 'ports': None, 'pcu_ids': [], 'boot_nonce': None, 'node_id': 1, 'root_person_ids': [], 'key': None, 'date_created': 1162884349, 'model': None, 'conf_file_ids': [], 'ssh_rsa_key': None}

#        current_peer_nodes = []
#        print 'current_peer_nodes',current_peer_nodes

        nb_new_nodes = peer.refresh_nodes(current_peer_nodes)

	return nb_new_nodes
