from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.ConfFiles import ConfFile, ConfFiles
from PLC.Auth import PasswordAuth

can_update = lambda (field, value): field not in \
             ['conf_file_id', 'source', 'dest', 'node_ids', 'nodegroup_ids']

class AddConfFile(Method):
    """
    Adds a new node configuration file. Any fields specified in
    conf_file_fields are used, otherwise defaults are used.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    conf_file_fields = dict(filter(can_update, ConfFile.fields.items()))

    accepts = [
        PasswordAuth(),
        conf_file_fields
        ]

    returns = Parameter(int, '1 if successful')

    event_type = 'Add'
    object_type = 'ConfFile'
    object_ids = []

    def call(self, auth, conf_file_fields = {}):
        conf_file_fields = dict(filter(can_update, conf_file_fields.items()))
        conf_file = ConfFile(self.api, conf_file_fields)
        conf_file.sync()

	self.object_ids = [conf_file['conf_file_id']]

        return 1
