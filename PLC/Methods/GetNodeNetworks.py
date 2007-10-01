from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.NodeNetworks import NodeNetwork, NodeNetworks
from PLC.Auth import Auth

class GetNodeNetworks(Method):
    """
    Returns an array of structs containing details about node network
    interfacess. If nodenetworks_filter is specified and is an array
    of node network identifiers, or a struct of node network
    fields and values, only node network interfaces matching the filter
    will be returned.

    If return_fields is given, only the specified details will be returned.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node', 'anonymous']

    accepts = [
        Auth(),
        Mixed([NodeNetwork.fields['nodenetwork_id']],
              Parameter (int, "nodenetwork id"),
              Filter(NodeNetwork.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [NodeNetwork.fields]
    
    def call(self, auth, nodenetwork_filter = None, return_fields = None):
        return NodeNetworks(self.api, nodenetwork_filter, return_fields)
