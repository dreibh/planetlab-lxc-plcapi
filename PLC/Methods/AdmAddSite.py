from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Sites import Site, Sites
from PLC.Auth import Auth
from PLC.Methods.AddSite import AddSite

can_update = lambda (field, value): field in \
             ['is_public', 'latitude', 'longitude', 'url']

class AdmAddSite(AddSite):
    """
    Deprecated. See AddSite.
    """

    status = "deprecated"

    site_fields = dict(filter(can_update, Site.fields.items()))

    accepts = [
        Auth(),
        Site.fields['name'],
        Site.fields['abbreviated_name'],
        Site.fields['login_base'],
        site_fields
        ]

    def call(self, auth, name, abbreviated_name, login_base, site_fields = {}):
        site_fields['name'] = name
        site_fields['abbreviated_name'] = abbreviated_name
        site_fields['login_base'] = login_base
        return AddSite.call(self, auth, site_fields)
