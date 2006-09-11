import os

from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Sites import Site, Sites
from PLC.Nodes import Node, Nodes
from PLC.Auth import PasswordAuth

class AdmGetSiteNodes(Method):
    """
    Return a dictionary containing a list of node_ids for the  sites specified.

    Admins may retrieve details about all nodes on a site by not specifying
    site_id_or_name or by specifying an empty list. Users and
    techs may only retrieve details about themselves. PIs may retrieve
    details about themselves and others at their sites.

    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        [Mixed(Site.fields['site_id'],
               Site.fields['name'])],
        Parameter([str], 'List of fields to return')
        ]

    # Filter out hidden fields
    #can_return = lambda (field, value): field not in ['deleted']
    #return_fields = dict(filter(can_return, Site.all_fields.items()))
    return_fields=['site_id', 'node_ids']
    returns = [return_fields]

    def __init__(self, *args, **kwds):
        Method.__init__(self, *args, **kwds)
        # Update documentation with list of default fields returned
        self.__doc__ += os.linesep.join(Site.default_fields.keys())

    def call(self, auth, site_id_or_name_list = None):
        # Authenticated function
        assert self.caller is not None
	#copy list of fields to return
	return_fields=self.return_fields

	#convert site_id_or_name_list to 'None' if is [] (empty list)
	if site_id_or_name_list is not None and site_id_or_name_list == []:
		site_id_or_name_list = None

        # Get site information
	sites = Sites(self.api, site_id_or_name_list, return_fields).values()	

	# make sure sites are found
	if not sites:
		raise PLCInvalidArgument, "No such site"
	elif site_id_or_name_list is None:
		pass
	elif not len(sites) == len(site_id_or_name_list):
		raise PLCInvalidArgument, "at least one site_id is invalid"

        # Filter out undesired or None fields (XML-RPC cannot marshal
        # None) and turn each node into a real dict.
        valid_return_fields_only = lambda (key, value): \
                                   key in return_fields and value is not None
        sites = [dict(filter(valid_return_fields_only, site.items())) \
                 for site in sites]
	
	#Convert list of sites dictionaries into a dictionary of sites -> sites:[node_ids]
	site_nodes = {}
	for site in sites:
		# Filter out deleted Nodes.  Nodes(...) will not reuturn deleted nodes
        	# XXX This shouldn't be necssary once the join tables are cleaned up
		nodes = Nodes(self.api, site['node_ids'])
		#creat valid node list dictionary
		site_nodes[str(site['site_id'])] = nodes.keys()
		
        return site_nodes
