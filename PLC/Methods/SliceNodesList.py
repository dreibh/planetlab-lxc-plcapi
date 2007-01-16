from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.Slices import Slice, Slices
from PLC.Nodes import Node, Nodes
from PLC.Methods.GetSlices import GetSlices

class SliceNodesList(Method):
    """
    Deprecated. Can be implemented with GetSlices.

    """
  
    status = "deprecated"

    roles = ['admin', 'pi', 'user']

    accepts = [
        Auth(),
        Slice.fields['name']
        ]

    returns = [Node.fields['hostname']]
    

    def call(self, auth, slice_name):
	# If we are not admin, make sure to return only viewable
	# slices.
	slices = GetSlices(self, auth, [slice_name])
	slice = slices[0]
	nodes = Nodes(self.api, slice['node_ids'])
	if not nodes:
	    return []
	
	node_hostnames = [node['hostname'] for node in nodes]		
	
        return node_hostnames
