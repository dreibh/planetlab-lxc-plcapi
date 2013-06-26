from types import StringTypes

from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.Nodes import Node, Nodes
from PLC.SliceTags import SliceTag, SliceTags
from PLC.Slices import Slice, Slices 

class RetrieveSliceSliverKeys(Method):
    """
    This method exposes the public ssh keys for a slice's slivers.
    It expects a slice name or id, and returns a dictionary on hostnames.
    This method is designed to help third-party software authenticate
    slivers (e.g. the OMF Experiment Controller). 
    For this reason it is accessible with anonymous authentication.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'anonymous' ]

    applicable_fields = {
        'slice_id' : Slice.fields['slice_id'],
        'name' : Slice.fields['name'],
        }

    accepts = [
        Auth(),
        Mixed(Slice.fields['slice_id'],
              Slice.fields['name']),
        Filter(Node.fields),
        ]

    returns = Parameter (dict, " ssh keys hashed on hostnames")

    def call(self, auth, slice_id_or_name, node_filter=None):
        
        filter={}
        if isinstance(slice_id_or_name,int):
            filter['slice_id']=slice_id_or_name
        elif isinstance(slice_id_or_name,StringTypes):
            filter['name']=slice_id_or_name
        filter['tagname']='ssh_key'
        # retrieve only sliver tags
        filter['~node_id']=None
        if node_filter:
            # make sure we only deal with local nodes
            node_filter['peer_id']=None
            nodes = Nodes(self.api, node_filter, ['node_id'])
            node_ids = [ node ['node_id'] for node in nodes ]
            filter['node_id']=node_ids
        
        # slice_tags don't expose hostname, sigh..
        slice_tags=SliceTags(self.api,filter,['node_id','tagname','value'])
        node_ids = [st['node_id'] for st in slice_tags]
        # fetch nodes
        nodes=Nodes(self.api,node_ids,['node_id','hostname'])
        # hash on node_id
        nodes_hash=dict( [ (n['node_id'],n['hostname']) for n in nodes])
        # return values hashed on hostname
        return dict([ (nodes_hash[st['node_id']],st['value']) for st in slice_tags])
