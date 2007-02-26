from PLC.Methods.GetNodeGroups import GetNodeGroups
 
class AnonAdmGetNodeGroups(GetNodeGroups):
    """
    Deprecated. See GetNodeGroups. All fields are now always returned
    """
    
    status = "deprecated"

    def call(self, auth, nodegroup_id_or_name_list =  None, return_fields = None):
	return GetNodeGroups.call(self, auth, nodegroup_id_or_name_list)
