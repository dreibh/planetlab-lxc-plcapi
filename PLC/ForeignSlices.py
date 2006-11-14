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

    def delete (self, commit=True):
        """
        Delete existing foreign slice.
        """
        self.purge_peer_slice()
        self['deleted']=True
        self.sync(commit)
        

class ForeignSlices (Table):
    def __init__ (self, api, foreign_slice_filter = None, columns = None):
        Table.__init__(self, api, ForeignSlice, columns)

        sql = ""
	sql += "SELECT %s FROM view_foreign_slices " % ", ".join(self.columns)
        sql += "WHERE deleted IS False "
              
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

    # managing an index by slicename
    def name_index(self):
        if 'name' not in self.columns:
            raise PLCFault,"ForeignSlices::name_index, name not selected"
        self.index={}
        for foreign_slice in self:
            self.index[foreign_slice['name']]=foreign_slice
            
    def name_add_by(self,foreign_slice):
        self.index[foreign_slice['name']]=foreign_slice

    def name_locate(self,name):
        return self.index[name]
            
