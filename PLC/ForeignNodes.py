#
# Thierry Parmentelat - INRIA
# 
import time

from types import StringTypes

from PLC.Table import Row, Table
from PLC.Parameter import Parameter
from PLC.Filter import Filter

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
        'slice_ids': Parameter([int], "List of slices on this node"),
	}

    def __init__(self,api,fields={},uptodate=True):
	Row.__init__(self,api,fields)
	self.uptodate=uptodate

    def validate_date_created(self,timestamp):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timestamp))

    def validate_last_updated(self,timestamp):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timestamp))

    def purge_peer_node (self,commit=True):
        sql = "DELETE FROM peer_node WHERE node_id=%d"%self['node_id']
        self.api.db.do(sql)
        if commit:
            self.api.db.commit()

    def delete (self, commit=True):
        """
        Delete existing foreign node.
        """
        self.purge_peer_node()
        self['deleted']=True
        self.sync(commit)
        
class ForeignNodes (Table):
    def __init__ (self, api, foreign_node_filter = None, columns = None):
        Table.__init__(self, api, ForeignNode, columns)

        sql = ""
	sql += "SELECT %s FROM view_foreign_nodes " % ", ".join(self.columns)
        sql += "WHERE deleted IS False "
              
        if foreign_node_filter is not None:
            if isinstance(foreign_node_filter, (list, tuple, set)):
                # Separate the list into integers and strings
                ints = filter(lambda x: isinstance(x, (int, long)), foreign_node_filter)
                strs = filter(lambda x: isinstance(x, StringTypes), foreign_node_filter)
                foreign_node_filter = Filter(ForeignNode.fields, {'node_id': ints, 'hostname': strs})
                sql += " AND (%s)" % foreign_node_filter.sql(api, "OR")
            elif isinstance(foreign_node_filter, dict):
                foreign_node_filter = Filter(ForeignNode.fields, foreign_node_filter)
                sql += " AND (%s)" % foreign_node_filter.sql(api, "AND")

	self.selectall(sql)

