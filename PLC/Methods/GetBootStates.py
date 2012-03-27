from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.BootStates import BootState, BootStates
from PLC.Auth import Auth

class GetBootStates(Method):
    """
    Returns an array of all valid node boot states.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node']

    accepts = [
        Auth()
        ]

    returns = [BootState.fields['boot_state']]


    def call(self, auth):
        return [boot_state['boot_state'] for boot_state in BootStates(self.api)]
