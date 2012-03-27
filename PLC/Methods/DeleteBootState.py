from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.BootStates import BootState, BootStates
from PLC.Auth import Auth

class DeleteBootState(Method):
    """
    Deletes a node boot state.

    WARNING: This will cause the deletion of all nodes in this boot
    state.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        BootState.fields['boot_state']
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, name):
        boot_states = BootStates(self.api, [name])
        if not boot_states:
            raise PLCInvalidArgument, "No such boot state"
        boot_state = boot_states[0]

        boot_state.delete()

        return 1
