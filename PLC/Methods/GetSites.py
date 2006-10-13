import os

from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import PasswordAuth
from PLC.Sites import Site, Sites

class GetSites(Method):
    """
    Return an array of structs containing details about all sites. If
    site_id_list is specified, only the specified sites will be
    queried.

    If return_fields is specified, only the specified fields will be
    returned, if set. Otherwise, the default set of fields returned is:

    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        [Mixed(Site.fields['site_id'],
               Site.fields['login_base'])]
        ]

    returns = [Site.fields]

    event_type = 'Get'
    object_type = 'Site'
	
    def __init__(self, *args, **kwds):
        Method.__init__(self, *args, **kwds)
        # Update documentation with list of default fields returned
        self.__doc__ += os.linesep.join(Site.fields.keys())

    def call(self, auth, site_id_or_login_base_list = None):
        
        # Get site information
        sites = Sites(self.api, site_id_or_login_base_list)

        # turn each site into a real dict.
        sites = [dict(site.items()) for site in sites.values()]
	
        return sites
