from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.BootStates import BootState, BootStates
from PLC.Auth import Auth

class AddBootState(Method):
    """
    Adds a new node boot state.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        BootState.fields['boot_state']
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, name):
        boot_state = BootState(self.api)
        boot_state['boot_state'] = name
        boot_state.sync(insert = True)

        return 1
