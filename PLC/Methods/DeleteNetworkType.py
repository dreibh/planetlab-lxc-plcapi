from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NetworkTypes import NetworkType, NetworkTypes
from PLC.Auth import Auth

class DeleteNetworkType(Method):
    """
    Deletes a network type.

    WARNING: This will cause the deletion of all network interfaces
    that use this type.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        NetworkType.fields['type']
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, name):
        network_types = NetworkTypes(self.api, [name])
        if not network_types:
            raise PLCInvalidArgument, "No such network type"
        network_type = network_types[0]

        network_type.delete()

        return 1
