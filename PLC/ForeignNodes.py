#
# Thierry Parmentelat - INRIA
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

    def __init__ (self, api, foreign_node_id_or_hostname_list=None):

	self.api=api

	sql =""
	sql += "SELECT %s FROM foreign_nodes " % ", ".join(ForeignNode.fields)
	sql += "WHERE foreign_nodes.deleted IS False " 

	if foreign_node_id_or_hostname_list:
	    foreign_node_id_list = [ str(x) for x in foreign_node_id_or_hostname_list 
				     if isinstance(x, (int,long))]
	    hostname_list = [ x for x in foreign_node_id_or_hostname_list
			      if isinstance(x, StringTypes)]
	    sql += " AND (False"
	    if foreign_node_id_list:
		sql += " OR foreign_node_id in (%s)" % ", ".join(foreign_node_id_list)
	    if hostname_list:
		## figure how to retrieve peer_id from the hostname(s)
		sql += " OR hostname IN (%s)" % ", ".join(api.db.quote(hostname_list))
	    sql += ")"

	rows = self.api.db.selectall (sql)

	for row in rows:
	    self[row['hostname']] = ForeignNode (api,row)


	
