# $Id$
# $URL$
from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.NodeGroups import NodeGroup, NodeGroups

class v43GetNodeGroups(Method):
    """
    Returns an array of structs containing details about node groups.
    If nodegroup_filter is specified and is an array of node group
    identifiers or names, or a struct of node group attributes, only
    node groups matching the filter will be returned. If return_fields
    is specified, only the specified details will be returned.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node', 'anonymous']

    accepts = [
        Auth(),
        Mixed([Mixed(NodeGroup.fields['nodegroup_id'],
                     NodeGroup.fields['groupname'])],
              Filter(NodeGroup.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [NodeGroup.fields]
  
    def call(self, auth, nodegroup_filter = None, return_fields = None):
	return NodeGroups(self.api, nodegroup_filter, return_fields)


nodegroup_fields = NodeGroup.fields.copy()
nodegroup_fields['name'] = Parameter(str, "Legacy version of groupname", max = 50),

class v42GetNodeGroups(v43GetNodeGroups):
    """
    Legacy wrapper for v42GetNodeGroups.
    """

    accepts = [
        Auth(),
        Mixed([Mixed(NodeGroup.fields['nodegroup_id'],
                     NodeGroup.fields['groupname'])],
              Filter(nodegroup_fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [nodegroup_fields]
  
    def call(self, auth, nodegroup_filter = None, return_fields = None):
        # convert name -> groupname in both filters
        if isinstance(nodegroup_filter, dict):
            if nodegroup_filter.has_key('name'):
                groupname = nodegroup_filter.pop('name')
                if not nodegroup_filter.has_key('groupname'):
                    nodegroup_filter['groupname']=groupname

        if isinstance(return_fields, list):
            if 'name' in return_fields:
                return_fields.remove('name')
                if 'groupname' not in return_fields:
                    return_fields.append('groupname')

        nodegroups = NodeGroups(self.api, nodegroup_filter, return_fields)
        # if groupname is present, then create a name mapping
        for nodegroup in nodegroups:
            if nodegroup.has_key('groupname'):
                nodegroup['name']=nodegroup['groupname']
        return nodegroups

class GetNodeGroups(v42GetNodeGroups):
    """
    Returns an array of structs containing details about node groups.
    If nodegroup_filter is specified and is an array of node group
    identifiers or names, or a struct of node group attributes, only
    node groups matching the filter will be returned. If return_fields
    is specified, only the specified details will be returned.
    """

    pass
