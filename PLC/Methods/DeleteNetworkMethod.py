from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.NetworkMethods import NetworkMethod, NetworkMethods
from PLC.Auth import Auth

class DeleteNetworkMethod(Method):
    """
    Deletes a network method.

    WARNING: This will cause the deletion of all network interfaces
    that use this method.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        NetworkMethod.fields['method']
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, name):
        network_methods = NetworkMethods(self.api, [name])
        if not network_methods:
            raise PLCInvalidArgument, "No such network method"
        network_method = network_methods[0]

        network_method.delete()

        return 1
