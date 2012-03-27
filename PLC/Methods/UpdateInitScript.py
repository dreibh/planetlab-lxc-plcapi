from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.InitScripts import InitScript, InitScripts
from PLC.Auth import Auth

can_update = lambda (field, value): field not in \
             ['initscript_id']

class UpdateInitScript(Method):
    """
    Updates an initscript. Only the fields specified in
    initscript_fields are updated, all other fields are left untouched.

    Returns 1 if successful, faults otherwise.
    """

    roles = ['admin']

    initscript_fields = dict(filter(can_update, InitScript.fields.items()))

    accepts = [
        Auth(),
        InitScript.fields['initscript_id'],
        initscript_fields
        ]

    returns = Parameter(int, '1 if successful')

    def call(self, auth, initscript_id, initscript_fields):
        initscript_fields = dict(filter(can_update, initscript_fields.items()))

        initscripts = InitScripts(self.api, [initscript_id])
        if not initscripts:
            raise PLCInvalidArgument, "No such initscript"

        initscript = initscripts[0]
        initscript.update(initscript_fields)
        initscript.sync()
        self.event_objects = {'InitScript': [initscript['initscript_id']]}

        return 1
