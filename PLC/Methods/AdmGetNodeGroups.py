import os

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Sites import Site, Sites
from PLC.Nodes import Node, Nodes
from PLC.Auth import PasswordAuth
from PLC.NodeGroups import NodeGroup, NodeGroups
class AdmGetNodeGroups(Method):
    """
    Returns a list of structs containing the details about the node groups 
    specified. 

    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        [Mixed(NodeGroup.fields['nodegroup_id'],
	       NodeGroup.fields['name'])]
        ]

    returns = [NodeGroup.all_fields]
  
    def __init__(self, *args, **kwds):
        Method.__init__(self, *args, **kwds)
        # Update documentation with list of default fields returned
        self.__doc__ += os.linesep.join(Site.default_fields.keys())

    def call(self, auth, nodegroup_id_or_name_list=None):
        # Authenticated function
        assert self.caller is not None

        # Get nodes in this nodegroup
	nodegroups = NodeGroups(self.api, nodegroup_id_or_name_list).values()	

	# make sure sites are found
	if not nodegroups:
		raise PLCInvalidArgument, "No such site"
	elif nodegroup_id_or_name_list is None:
		pass
	elif not len(nodegroups) == len(nodegroup_id_or_name_list):
		raise PLCInvalidArgument, "at least one node group id is invalid"
	
	# Filter out undesired or None fields (XML-RPC cannot marshal
        # None) and turn each node into a real dict.
        valid_return_fields_only = lambda (key, value): \
                                   key in NodeGroup.all_fields and value is not None
        nodegroups = [dict(filter(valid_return_fields_only, nodegroup.items())) \
                 for nodegroup in nodegroups]

        return nodegroups
