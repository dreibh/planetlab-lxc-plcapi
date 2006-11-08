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
    
    Returns None
    """
    
    roles = ['admin']
    
    accepts = [ Auth(),
		Parameter (int, "Peer id") ]
    
    returns = None

    def call (self, auth, peer_id):
	
	### retrieve peer info
	peers = Peers (self.api)
	peer = peers[peer_id]
	
	### retrieve account info
	person_id = peer['person_id']
	persons = Persons (self.api,[person_id])
	person = persons[person_id]
	
	### build up foreign auth
	auth={ 'Username': person['email'],
	       'AuthMethod' : 'password',
	       'AuthString' : person['password'],
	       'Role' : 'admin' }

	## connect to the peer's API
	apiserver = xmlrpclib.Server (peer['peer_url']+"/PLCAPI/")
	print 'auth',auth
	current_peer_nodes = apiserver.GetNodes(auth,[])
	
	## manual feed for tests
#	n1 = {'hostname': 'n1.plc', 'boot_state': 'inst'}
#	n2 = {'hostname': 'n2.plc', 'boot_state': 'inst'}
#	n3 = {'hostname': 'n3.plc', 'boot_state': 'inst'}
        n11={'session': None, 'slice_ids': [], 'nodegroup_ids': [], 'last_updated': 1162884349, 'version': None, 'nodenetwork_ids': [], 'boot_state': 'inst', 'hostname': 'n11.plc1.org', 'site_id': 1, 'ports': None, 'pcu_ids': [], 'boot_nonce': None, 'node_id': 1, 'root_person_ids': [], 'key': None, 'date_created': 1162884349, 'model': None, 'conf_file_ids': [], 'ssh_rsa_key': None}
        n12={'session': None, 'slice_ids': [], 'nodegroup_ids': [], 'last_updated': 1162884349, 'version': None, 'nodenetwork_ids': [], 'boot_state': 'inst', 'hostname': 'n12.plc1.org', 'site_id': 1, 'ports': None, 'pcu_ids': [], 'boot_nonce': None, 'node_id': 1, 'root_person_ids': [], 'key': None, 'date_created': 1162884349, 'model': None, 'conf_file_ids': [], 'ssh_rsa_key': None}
        n21={'session': None, 'slice_ids': [], 'nodegroup_ids': [], 'last_updated': 1162884349, 'version': None, 'nodenetwork_ids': [], 'boot_state': 'boot', 'hostname': 'n21.plc2.org', 'site_id': 1, 'ports': None, 'pcu_ids': [], 'boot_nonce': None, 'node_id': 1, 'root_person_ids': [], 'key': None, 'date_created': 1162884349, 'model': None, 'conf_file_ids': [], 'ssh_rsa_key': None}
        n22={'session': None, 'slice_ids': [], 'nodegroup_ids': [], 'last_updated': 1162884349, 'version': None, 'nodenetwork_ids': [], 'boot_state': 'boot', 'hostname': 'n22.plc2.org', 'site_id': 1, 'ports': None, 'pcu_ids': [], 'boot_nonce': None, 'node_id': 1, 'root_person_ids': [], 'key': None, 'date_created': 1162884349, 'model': None, 'conf_file_ids': [], 'ssh_rsa_key': None}

#        current_peer_nodes = [n21,n22]

	### now to the db
	# we get the whole table just in case 
	# a host would have switched from one plc to the other
	foreign_nodes = ForeignNodes (self.api)
	
	### mark entries for this peer outofdate
	for foreign_node in foreign_nodes.values():
	    if foreign_node['peer_id'] == peer_id:
		foreign_node.uptodate=False

        ### these fields get copied through
        remote_fields = ['boot_state','model','version','date_created','date_updated']
        
	### scan the new entries, and mark them uptodate
	for node in current_peer_nodes:
	    hostname = node['hostname']
	    foreign_node = foreign_nodes.get(hostname)
	    if foreign_node:
		### update it anyway
                foreign_node['cached'] = True
		foreign_node['peer_id'] = peer_id
                # copy other relevant fields
                for field in remote_fields:
                    foreign_node[field]=node[field]
                # this row is valid
		foreign_node.uptodate = True
	    else:
		foreign_nodes[hostname] = ForeignNode(self.api,
						      {'hostname':hostname,
                                                       'cached':True,
						       'peer_id':peer_id,})
                for field in remote_fields:
                    foreign_nodes[hostname][field]=node[field]
                    
	    foreign_nodes[hostname].sync()

	### delete entries that are not uptodate
	[ x.delete() for x in foreign_nodes.values() if not x.uptodate ]
	
