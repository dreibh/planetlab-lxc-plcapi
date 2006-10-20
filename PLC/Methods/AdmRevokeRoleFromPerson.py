from PLC.Methods.DeleteRoleFromPerson import DeleteRoleFromPerson

class AdmRevokeRoleFromPerson(DeleteRoleFromPerson):
    """
    Deprecated. See DeleteRoleFromPerson.
    """

    status = "deprecated"

    def call(self, auth, person_id_or_email, role_id_or_name):
        return DeleteRoleFromPerson.call(self, auth, role_id_or_name, person_id_or_email)
