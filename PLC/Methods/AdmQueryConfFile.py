from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Nodes import Node, Nodes
from PLC.ConfFiles import ConfFile, ConfFiles
from PLC.Auth import PasswordAuth

class AdmQueryConfFile(Method):
    """
    Deprecated. See GetConfFiles.
    """

    status = "deprecated"

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth(),
        {'node_id': Node.fields['node_id']}
        ]

    returns = [ConfFile.fields['conf_file_id']]

    def call(self, auth, search_vals):
        if 'node_id' in search_vals:
            conf_files = ConfFiles(self.api).values()

            conf_files = filter(lambda conf_file: \
                                search_vals['node_id'] in conf_file['node_ids'],
                                conf_files)

            if conf_files:
                return [conf_file['conf_file_id'] for conf_file in conf_files]

        return []
