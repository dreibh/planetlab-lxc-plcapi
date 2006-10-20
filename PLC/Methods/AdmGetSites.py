from PLC.Methods.GetSites import GetSites

class AdmGetSites(GetSites):
    """
    Deprecated. See GetSites.
    """

    status = "deprecated"

    def call(self, auth, site_id_or_login_base_list = None, return_fields = None):
        return GetSites.call(self, auth, site_id_or_login_base_list)
