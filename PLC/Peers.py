import re

from types import StringTypes

from PLC.Faults import *
from PLC.Parameter import Parameter
from PLC.Table import Row, Table

class Peer (Row):
    """
    Stores the list of peering PLCs in the peers table. 
    See the Row class for more details
    """

    table_name = 'peers'
    primary_key = 'peer_id'
    fields = {
	'peer_id' : Parameter (int, "Peer identifier"),
	'peername' : Parameter (str, "Peer name"),
	'peer_url' : Parameter (str, "Peer API url"),
	'person_id' : Parameter (int, "person_id of the account used to log there"),
	'foreign_node_ids' : Parameter ([int], "doc")
	}

    def validate_peer_url (self, url):
	"""
	Validate URL, checks it looks like https 
	"""
	invalid_url = PLCInvalidArgument("Invalid URL")
	if not re.compile ("^https://.*$").match(url) : 
	    raise invalid_url
	return url

    def delete (self, commit=True):
	"""
	Delete peer
	"""
	
	assert 'peer_id' in self

	self['deleted'] = True
	self.sync(commit)

class Peers (Table):
    """ 
    Maps to the peers table in the database
    """
    
    def __init__ (self, api, peer_id_or_peername_list = None):
	self.api = api

	sql="SELECT %s FROM view_peers WHERE deleted IS False" % \
	    ", ".join(Peer.fields)
	if peer_id_or_peername_list:
            peer_ids = [x for x in peer_id_or_peername_list if isinstance(x, (int, long))]
            peernames = [x for x in peer_id_or_peername_list if isinstance(x, StringTypes)]
	    sql += " AND (False"
	    if peer_ids:
		sql += " OR peer_id in (%s)"% ", ".join([str(i) for i in peer_ids])
	    if peernames:
		sql += " OR peername in (%s)"% ". ".join(api.db.quote(peernames)).lower()
	    sql += ")"

	rows = self.api.db.selectall(sql)

	for row in rows:
	    self[row['peer_id']] = peer = Peer(api,row)
            for aggregate in ['foreign_node_ids']:
                if not peer.has_key(aggregate) or peer[aggregate] is None:
                    peer[aggregate] = []
                else:
                    peer[aggregate] = map(int, peer[aggregate].split(','))


