from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import PasswordAuth, BootAuth

class BootUpdateNode(Method):
    """
    Allows the calling node to update its own record. Only the primary
    network can be updated, and the node IP cannot be changed.

    Returns 1 if updated successfully.
    """

    accepts = [BootAuth(), dict]
    returns = Parameter(int, '1 if successful')

    def call(self, auth, update_fields):
        # XXX
        return 1
