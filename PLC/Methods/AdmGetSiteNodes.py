from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Sites import Site, Sites
from PLC.Auth import Auth

class AdmGetSiteNodes(Method):
    """
    Deprecated. See GetSites.

    Return a struct containing an array of node_ids for each of the
    sites specified. Note that the keys of the struct are strings, not
    integers, because of XML-RPC marshalling limitations.

    Admins may retrieve details about all nodes on a site by not specifying
    site_id_or_name or by specifying an empty list. Users and
    techs may only retrieve details about themselves. PIs may retrieve
    details about themselves and others at their sites.
    """

    status = "deprecated"

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        Auth(),
        [Mixed(Site.fields['site_id'],
               Site.fields['name'])],
        ]

    returns = dict

    def call(self, auth, site_id_or_name_list = None):
        # Get site information
	sites = Sites(self.api, site_id_or_name_list)	
	if not sites:
            raise PLCInvalidArgument, "No such site"
        
	# Convert to {str(site_id): [node_id]}
	site_nodes = {}
	for site in sites:
            site_nodes[str(site['site_id'])] = site['node_ids']
		
        return site_nodes
