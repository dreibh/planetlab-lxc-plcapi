#
# the nodes standing on peer plc's
#
# Thierry Parmentelat
# 

from types import StringTypes

from PLC.Table import Row, Table
from PLC.Parameter import Parameter

class ForeignNode (Row) :
    """
    This object stores information about nodes hosted on 
    other peering instances of myplc
    """

    table_name = 'foreign_nodes'
    primary_key = 'foreign_node_id'

    fields = {
	'foreign_node_id': Parameter (int, "Foreign Node Id"),
	'hostname': Parameter (str, "Node name"),
	'boot_state' : Parameter (str, "Boot state"),
	'peer_id': Parameter (str, "Peer id"),
	}

    def __init__(self,api,fields={},uptodate=True):
	Row.__init__(self,api,fields)
	self.uptodate=uptodate

class ForeignNodes (Table):

    def __init__ (self, api, foreign_node_id_or_peername_list=None):

	self.api=api

	# must qualify fields because peer_id otherwise gets ambiguous
	fields = ["foreign_nodes.%s"%x for x in ForeignNode.fields]
		  
	sql =""
	sql += "SELECT %s FROM foreign_nodes, peers " % ", ".join(fields)
	sql += "WHERE foreign_nodes.peer_id=peers.peer_id "
	sql += "AND foreign_nodes.deleted IS False " 

	if foreign_node_id_or_peername_list:
	    foreign_node_id_list = [ x for x in foreign_node_id_or_peername_list if isinstance(x, (int,long))]
	    peername_list = [ x for x in foreign_node_id_or_peername_list if isinstance(x, StringTypes)]
	    sql += " AND (False"
	    if foreign_node_id_list:
		sql += " OR foreign_node_id in (%s)" % ", ".join([str(i) for i in foreign_node_id_list])
	    if peername_list:
		## figure how to retrieve peer_id from the peername(s)
		sql += " OR peername IN (%s)" % ", ".join(api.db.quote(peername_list))
	    sql += ")"

	rows = self.api.db.selectall (sql)

	for row in rows:
	    self[row['hostname']] = ForeignNode (api,row)


	
