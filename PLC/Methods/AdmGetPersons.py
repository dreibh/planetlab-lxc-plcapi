from PLC.Methods.GetPersons import GetPersons

class AdmGetPersons(GetPersons):
    """
    Deprecated. See GetPersons.
    """

    status = "deprecated"

    def call(self, auth, person_id_or_email_list = None, return_fields = None):
        return GetPersons.call(self, auth, person_id_or_email_list)
