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

    table_name = 'nodes'
    primary_key = 'node_id'

    fields = {
	'node_id': Parameter (int, "Node Id"),
	'hostname': Parameter (str, "Node name"),
	'peer_id': Parameter (str, "Peer id"),
	'boot_state' : Parameter (str, "Boot state, see Node"),
        'model' : Parameter (str,"Model, see Node"),
        'version' : Parameter (str,"Version, see Node"),
        'date_created': Parameter(int, "Creation time, see Node"),
        'last_updated': Parameter(int, "Update time, see Node"),
	}

    def __init__(self,api,fields={},uptodate=True):
	Row.__init__(self,api,fields)
	self.uptodate=uptodate

    def delete (self, commit=True):
        """
        Delete existing foreign node.
        """
        print 'in ForeignNode::delete',self
        self['deleted']=True
        self.sync(commit)
        

class ForeignNodes (Table):

    def __init__ (self, api, foreign_node_id_or_hostname_list=None):

	self.api=api

	sql =""
	sql += "SELECT %s FROM view_foreign_nodes " % ", ".join(ForeignNode.fields)
	sql += "WHERE view_foreign_nodes.deleted IS False " 

	if foreign_node_id_or_hostname_list:
	    foreign_node_id_list = [ str(x) for x in foreign_node_id_or_hostname_list 
				     if isinstance(x, (int,long))]
	    hostname_list = [ x for x in foreign_node_id_or_hostname_list
			      if isinstance(x, StringTypes)]
	    sql += " AND (False"
	    if foreign_node_id_list:
		sql += " OR node_id in (%s)" % ", ".join(foreign_node_id_list)
	    if hostname_list:
		## figure how to retrieve peer_id from the hostname(s)
		sql += " OR hostname IN (%s)" % ", ".join(api.db.quote(hostname_list))
	    sql += ")"

	rows = self.api.db.selectall (sql)

	for row in rows:
	    self[row['hostname']] = ForeignNode (api,row)


	
