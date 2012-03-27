from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NetworkTypes import NetworkType, NetworkTypes
from PLC.Auth import Auth

class AddNetworkType(Method):
    """
    Adds a new network type.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        NetworkType.fields['type']
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, name):
        network_type = NetworkType(self.api)
        network_type['type'] = name
        network_type.sync(insert = True)

        return 1
