from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.ConfFiles import ConfFile, ConfFiles
from PLC.Auth import PasswordAuth

class GetConfFiles(Method):
    """
    Returns an array of structs containing details about node
    configuration files. If conf_file_ids is specified, only the
    specified configuration files will be queried.
    """

    roles = ['admin']

    accepts = [
        PasswordAuth(),
        [ConfFile.fields['conf_file_id']]
        ]

    returns = [ConfFile.fields]

    def call(self, auth, conf_file_ids = None):
        conf_files = ConfFiles(self.api, conf_file_ids).values()
        conf_files = [dict(conf_file) for conf_file in conf_files]
        return conf_files
