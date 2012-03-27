from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.ConfFiles import ConfFile, ConfFiles
from PLC.Auth import Auth

can_update = lambda (field, value): field not in \
             ['conf_file_id', 'node_ids', 'nodegroup_ids']

class UpdateConfFile(Method):
    """
    Updates a node configuration file. Only the fields specified in
    conf_file_fields are updated, all other fields are left untouched.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    conf_file_fields = dict(filter(can_update, ConfFile.fields.items()))

    accepts = [
        Auth(),
        ConfFile.fields['conf_file_id'],
        conf_file_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, conf_file_id, conf_file_fields):
        conf_file_fields = dict(filter(can_update, conf_file_fields.items()))

        conf_files = ConfFiles(self.api, [conf_file_id])
        if not conf_files:
            raise PLCInvalidArgument, "No such configuration file"

        conf_file = conf_files[0]
        conf_file.update(conf_file_fields)
        conf_file.sync()
        self.event_objects = {'ConfFile': [conf_file['conf_file_id']]}

        return 1
