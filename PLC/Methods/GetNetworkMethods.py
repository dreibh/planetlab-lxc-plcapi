from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NetworkMethods import NetworkMethod, NetworkMethods
from PLC.Auth import Auth

class GetNetworkMethods(Method):
    """
    Returns a list of all valid network methods.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        Auth()
        ]

    returns = [NetworkMethod.fields['method']]

    event_type = 'Get'
    object_type = 'NetworkMethod'

    def call(self, auth):
        return [network_method['method'] for network_method in NetworkMethods(self.api)]
