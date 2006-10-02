import os

from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import PasswordAuth
from PLC.Sites import Site, Sites

class AdmGetSites(Method):
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
               Site.fields['login_base'])],
        Parameter([str], 'List of fields to return')
        ]

    returns = [Site.fields]

    def __init__(self, *args, **kwds):
        Method.__init__(self, *args, **kwds)
        # Update documentation with list of default fields returned
        self.__doc__ += os.linesep.join(Site.fields.keys())

    def call(self, auth, site_id_or_login_base_list = None, return_fields = None):
        # Make sure that only valid fields are specified
        if return_fields is None:
            return_fields = Site.fields
        elif filter(lambda field: field not in Site.fields, return_fields):
            raise PLCInvalidArgument, "Invalid return field specified"

        # Get site information
        sites = Sites(self.api, site_id_or_login_base_list, return_fields)

        # Filter out undesired or None fields (XML-RPC cannot marshal
        # None) and turn each site into a real dict.
        valid_return_fields_only = lambda (key, value): \
                                   key in return_fields and value is not None
        sites = [dict(filter(valid_return_fields_only, site.items())) \
                 for site in sites.values()]

        return sites
