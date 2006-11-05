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


class UpdatePeer(Method):
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
#	current_peer_nodes = [n2,n3]

	### now to the db
	# we get the whole table just in case 
	# a host would have switched from one plc to the other
	foreign_nodes = ForeignNodes (self.api)
	
	### mark entries for this peer outofdate
	for foreign_node in foreign_nodes.values():
	    if foreign_node['peer_id'] == peer_id:
		foreign_node.uptodate=False

	### scan the new entries, and mark them uptodate
	for node in current_peer_nodes:
	    hostname = node['hostname']
	    foreign_node = foreign_nodes.get(hostname)
	    if foreign_node:
		### update it anyway
		foreign_node['peer_id'] = peer_id
		foreign_node['boot_state'] = node['boot_state']
		foreign_node.uptodate = True
	    else:
		foreign_nodes[hostname] = ForeignNode(self.api,
						      {'hostname':hostname,
						       'boot_state':node['boot_state'],
						       'peer_id':peer_id})
	    foreign_nodes[hostname].sync()

	### delete entries that are not uptodate
	[ x.delete() for x in foreign_nodes.values() if not x.uptodate ]
	
