#
# Thierry Parmentelat - INRIA
# 

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth

from PLC.ForeignNodes import ForeignNode, ForeignNodes

class GetForeignNodes(Method):
    """
    Returns an array of structs containing details about foreign
    nodes. If foreign_node_filter is specified and is an array of
    foreign node identifiers or hostnames, or a struct of foreign node
    attributes, only foreign nodes matching the filter will be
    returned. If return_fields is specified, only the specified
    details will be returned.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Mixed([Mixed(ForeignNode.fields['node_id'],
                     ForeignNode.fields['hostname'])],
              Filter(ForeignNode.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]
    
    returns = [ForeignNode.fields]

    def call(self, auth, foreign_node_filter = None, return_fields = None):
	return ForeignNodes(self.api, foreign_node_filter, return_fields)
