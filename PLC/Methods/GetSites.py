from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.Auth import Auth
from PLC.Sites import Site, Sites

class GetSites(Method):
    """
    Returns an array of structs containing details about sites. If
    site_filter is specified and is an array of site identifiers or
    hostnames, or a struct of site attributes, only sites matching the
    filter will be returned. If return_fields is specified, only the
    specified details will be returned.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node', 'anonymous']

    accepts = [
        Auth(),
        Mixed([Mixed(Site.fields['site_id'],
                     Site.fields['login_base'])],
              Parameter(str,"login_base"),
              Parameter(int,"site_id"),
              Filter(Site.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [Site.fields]

    def call(self, auth, site_filter = None, return_fields = None):
        return Sites(self.api, site_filter, return_fields)
