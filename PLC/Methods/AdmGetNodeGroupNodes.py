import os

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Sites import Site, Sites
from PLC.Nodes import Node, Nodes
from PLC.Auth import PasswordAuth
from PLC.NodeGroups import NodeGroup, NodeGroups
class AdmGetNodeGroupNodes(Method):
    """
    Return a list of node_ids for the node group specified.

    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        Mixed(NodeGroup.fields['nodegroup_id'],
	      NodeGroup.fields['name'])
        ]

    returns = [NodeGroup.join_fields['node_ids']]

    def __init__(self, *args, **kwds):
        Method.__init__(self, *args, **kwds)
        # Update documentation with list of default fields returned
        self.__doc__ += os.linesep.join(Site.default_fields.keys())

    def call(self, auth, nodegroup_id_or_name):
        # Authenticated function
        assert self.caller is not None

        # Get nodes in this nodegroup
	nodegroup = NodeGroups(self.api, [nodegroup_id_or_name])	

	# make sure sites are found
	if not nodegroup:
		raise PLCInvalidArgument, "No such site"
	
	#get the info for the node group specified
	nodegroup_values = nodegroup.values()[0]

	#grab the list of node ides fromt the disctioary
	node_ids = nodegroup_values['node_ids']
	
        return node_ids
