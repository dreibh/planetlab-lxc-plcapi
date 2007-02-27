from PLC.Methods.GetNodes import GetNodes

class AdmGetNodes(GetNodes):
    """
    Deprecated. See GetNodes. All fields are now always returned.
    """

    status = "deprecated"

    def call(self, auth, node_id_or_hostname_list = None, return_fields = None):
        return GetNodes.call(self, auth, node_id_or_hostname_list)
