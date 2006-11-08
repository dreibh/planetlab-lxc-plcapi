from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.ConfFiles import ConfFile, ConfFiles
from PLC.Auth import Auth

class GetConfFiles(Method):
    """
    Returns an array of structs containing details about configuration
    files. If conf_file_filter is specified and is an array of
    configuration file identifiers, or a struct of configuration file
    attributes, only configuration files matching the filter will be
    returned.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Mixed([ConfFile.fields['conf_file_id']],
              Filter(ConfFile.fields))
        ]

    returns = [ConfFile.fields]

    def call(self, auth, conf_file_filter = None):
        return ConfFiles(self.api, conf_file_filter).values()
