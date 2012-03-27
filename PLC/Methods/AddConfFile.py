from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.ConfFiles import ConfFile, ConfFiles
from PLC.Auth import Auth

can_update = lambda (field, value): field not in \
             ['conf_file_id', 'node_ids', 'nodegroup_ids']

class AddConfFile(Method):
    """
    Adds a new node configuration file. Any fields specified in
    conf_file_fields are used, otherwise defaults are used.

    Returns the new conf_file_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin']

    conf_file_fields = dict(filter(can_update, ConfFile.fields.items()))

    accepts = [
        Auth(),
        conf_file_fields
        ]

    returns = Parameter(int, 'New conf_file_id (> 0) if successful')


    def call(self, auth, conf_file_fields):
        conf_file_fields = dict(filter(can_update, conf_file_fields.items()))
        conf_file = ConfFile(self.api, conf_file_fields)
        conf_file.sync()

        self.event_objects = {'ConfFile': [conf_file['conf_file_id']]}

        return conf_file['conf_file_id']
