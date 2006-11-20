#
# Thierry Parmentelat - INRIA
# 
import time

from types import StringTypes

from PLC.Table import Row, Table
from PLC.Parameter import Parameter
from PLC.Filter import Filter

class ForeignSlice (Row) :
    """
    This object stores information about slices hosted on 
    other peering instances of myplc
    """

    table_name = 'slices'
    primary_key = 'slice_id'

    fields = {
	'slice_id': Parameter (int, "Slice Id"),
        'name' :    Parameter (str, "Slice name"),
	'peer_id': Parameter (str, "Peer id"),
        'instantiation': Parameter(str, "Slice instantiation state"),
        'url': Parameter(str, "URL further describing this slice", max = 254, nullok = True),
        'description': Parameter(str, "Slice description", max = 2048, nullok = True),
        'max_nodes': Parameter(int, "Maximum number of nodes that can be assigned to this slice"),
        'created': Parameter(int, "Date and time when slice was created, in seconds since UNIX epoch", ro = True),
        'expires': Parameter(int, "Date and time when slice expires, in seconds since UNIX epoch"),
        'node_ids' : Parameter([int], "List of nodes in this slice"),
        }

    def __init__(self,api,fields={},uptodate=True):
	Row.__init__(self,api,fields)
	self.uptodate=uptodate

    def validate_created(self,timestamp):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timestamp))

    def validate_expires(self,timestamp):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timestamp))

    def purge_peer_slice (self,commit=True):
        sql = "DELETE FROM peer_slice WHERE slice_id=%d"%self['slice_id']
        self.api.db.do(sql)
        if commit:
            self.api.db.commit()

    def purge_slice_node (self,commit=True):
        sql = "DELETE FROM slice_node WHERE slice_id=%d"%self['slice_id']
        self.api.db.do(sql)
        if commit:
            self.api.db.commit()

    def add_slice_nodes (self, node_ids, commit=True):
        slice_id = self['slice_id']
        ### xxx needs to be optimized
        ### tried to figure a way to use a single sql statement
        ### like: insert into table (x,y) values (1,2),(3,4);
        ### but apparently this is not supported under postgresql
        for node_id in node_ids:
            sql="INSERT INTO slice_node VALUES (%d,%d)"%(slice_id,node_id)
            self.api.db.do(sql)
        if commit:
            self.api.db.commit()

    def update_slice_nodes (self, node_ids):
        # xxx to be optimized
        # we could compute the (set) difference between
        # current and updated set of node_ids
        # and invoke the DB only based on that
        #
        # for now : clean all entries for this slice
        self.purge_slice_node()
        # and re-install new list
        self.add_slice_nodes (node_ids)

    def delete (self, commit=True):
        """
        Delete existing foreign slice.
        """
        self.purge_peer_slice()
        self['is_deleted']=True
        self.sync(commit)
        

class ForeignSlices (Table):
    def __init__ (self, api, foreign_slice_filter = None, columns = None):
        Table.__init__(self, api, ForeignSlice, columns)

        sql = ""
	sql += "SELECT %s FROM view_foreign_slices " % ", ".join(self.columns)
        sql += "WHERE is_deleted IS False "

        if foreign_slice_filter is not None:
            if isinstance(foreign_slice_filter, (list, tuple, set)):
                # Separate the list into integers and strings
                ints = filter(lambda x: isinstance(x, (int, long)), foreign_slice_filter)
                strs = filter(lambda x: isinstance(x, StringTypes), foreign_slice_filter)
                foreign_slice_filter = Filter(ForeignSlice.fields, {'slice_id': ints, 'name': strs})
                sql += " AND (%s)" % foreign_slice_filter.sql(api, "OR")
            elif isinstance(foreign_slice_filter, dict):
                foreign_slice_filter = Filter(ForeignSlice.fields, foreign_slice_filter)
                sql += " AND (%s)" % foreign_slice_filter.sql(api, "AND")

	self.selectall(sql)

