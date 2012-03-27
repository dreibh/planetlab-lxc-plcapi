from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.InitScripts import InitScript, InitScripts
from PLC.Auth import Auth

class DeleteInitScript(Method):
    """
    Deletes an existing initscript.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    accepts = [
        Auth(),
        Mixed(InitScript.fields['initscript_id'],
              InitScript.fields['name']),
        ]

    returns = Parameter(int, '1 if successful')


    def call(self, auth, initscript_id_or_name):
        initscripts = InitScripts(self.api, [initscript_id_or_name])
        if not initscripts:
            raise PLCInvalidArgument, "No such initscript"

        initscript = initscripts[0]
        initscript.delete()
        self.event_objects = {'InitScript':  [initscript['initscript_id']]}

        return 1
