from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth
from PLC.Sites import Site, Sites

class GetSites(Method):
    """
    Return an array of structs containing details about all sites. If
    site_id_list is specified, only the specified sites will be
    queried.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        Auth(),
        [Mixed(Site.fields['site_id'],
               Site.fields['login_base'])]
        ]

    returns = [Site.fields]

    event_type = 'Get'
    object_type = 'Site'
    object_ids = []
	
    def call(self, auth, site_id_or_login_base_list = None):
        return Sites(self.api, site_id_or_login_base_list).values()
