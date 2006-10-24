from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.ConfFiles import ConfFile, ConfFiles
from PLC.Auth import PasswordAuth

class DeleteConfFile(Method):
    """
    Returns an array of structs containing details about node
    configuration files. If conf_file_ids is specified, only the
    specified configuration files will be queried.
    """

    roles = ['admin']

    accepts = [
        PasswordAuth(),
        ConfFile.fields['conf_file_id']
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, conf_file_id):
        conf_files = ConfFiles(self.api, [conf_file_id]).values()
        if not conf_files:
            raise PLCInvalidArgument, "No such configuration file"

        conf_file = conf_files[0]
        conf_file.delete()

        return 1