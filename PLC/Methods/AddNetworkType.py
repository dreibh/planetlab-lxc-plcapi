from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NetworkTypes import NetworkType, NetworkTypes
from PLC.Auth import PasswordAuth

class AddNetworkType(Method):
    """
    Adds a new network type.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        PasswordAuth(),
        NetworkType.fields['type']
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, name):
        network_type = NetworkType(self.api)
        network_type['type'] = name
        network_type.sync()

        return 1
