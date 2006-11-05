#
# Thierry Parmentelat - INRIA
# 

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth

from PLC.ForeignNodes import ForeignNode, ForeignNodes

class GetForeignNodes (Method):
    """
    returns information on foreign nodes
    """

    roles = ['admin']

    accepts = [ Auth(),
		[ Mixed(ForeignNode.fields['foreign_node_id'],
			ForeignNode.fields['hostname'])]
		]
    
    returns = [ ForeignNode.fields]

    def call (self, auth, foreign_id_or_hostname_list = None):

	return ForeignNodes (self.api, foreign_id_or_hostname_list).values()
	
