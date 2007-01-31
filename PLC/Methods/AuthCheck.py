from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth, BootAuth

class AuthCheck(Method):
    """
    Returns 1 if the user or node authenticated successfully, faults
    otherwise.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node']
    accepts = [Auth()]
    returns = Parameter(int, '1 if successful')

    def call(self, auth):
        return 1
