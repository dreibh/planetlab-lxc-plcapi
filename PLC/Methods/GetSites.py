from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
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
        Mixed([Mixed(Site.fields['site_id'],
                     Site.fields['login_base'])],
              Filter(Site.fields))
        ]

    returns = [Site.fields]

    event_type = 'Get'
    object_type = 'Site'
    object_ids = []
	
    def call(self, auth, site_filter = None):
        return Sites(self.api, site_filter).values()
