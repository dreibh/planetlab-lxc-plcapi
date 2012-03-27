from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.NodeGroups import NodeGroup, NodeGroups

class GetNodeGroups(Method):
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
