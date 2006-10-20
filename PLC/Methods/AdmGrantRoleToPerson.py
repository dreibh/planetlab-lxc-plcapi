from PLC.Methods.AddRoleToPerson import AddRoleToPerson

class AdmGrantRoleToPerson(AddRoleToPerson):
    """
    Deprecated. See AddRoleToPerson.
    """

    status = "deprecated"

    def call(self, auth, person_id_or_email, role_id_or_name):
        return AddRoleToPerson.call(self, auth, role_id_or_name, person_id_or_email)
