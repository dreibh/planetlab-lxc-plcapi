from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NetworkMethods import NetworkMethod, NetworkMethods
from PLC.Auth import PasswordAuth

class GetNetworkMethods(Method):
    """
    Returns a list of all valid network methods.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth()
        ]

    returns = [NetworkMethod.fields['method']]

    def call(self, auth):
        return [network_method['method'] for network_method in NetworkMethods(self.api).values()]
