from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import PasswordAuth

class AuthCheck(Method):
    """
    Returns 1 if the user authenticated successfully, faults
    otherwise.
    """

    roles = ['admin', 'pi', 'user', 'tech']
    accepts = [PasswordAuth()]
    returns = Parameter(int, '1 if successful')

    def call(self, auth):
        return 1
