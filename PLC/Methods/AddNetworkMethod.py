from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NetworkMethods import NetworkMethod, NetworkMethods
from PLC.Auth import PasswordAuth

class AddNetworkMethod(Method):
    """
    Adds a new network method.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        PasswordAuth(),
        NetworkMethod.fields['method']
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, name):
        network_method = NetworkMethod(self.api)
        network_method['method'] = name
        network_method.sync()

        return 1
