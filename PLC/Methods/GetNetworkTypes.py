from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NetworkTypes import NetworkType, NetworkTypes
from PLC.Auth import PasswordAuth

class GetNetworkTypes(Method):
    """
    Returns a list of all valid network types.
    """

    roles = ['admin', 'pi', 'user', 'tech']

    accepts = [
        PasswordAuth()
        ]

    returns = [NetworkType.fields['type']]

    def call(self, auth):
        return [network_type['type'] for network_type in NetworkTypes(self.api).values()]
