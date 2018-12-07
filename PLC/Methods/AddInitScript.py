from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.InitScripts import InitScript, InitScripts
from PLC.Auth import Auth

can_update = lambda field_value: field_value[0] not in \
             ['initscript_id']

class AddInitScript(Method):
    """
    Adds a new initscript. Any fields specified in initscript_fields
    are used, otherwise defaults are used.

    Returns the new initscript_id (> 0) if successful, faults otherwise.
    """

    roles = ['admin']

    initscript_fields = dict(list(filter(can_update, list(InitScript.fields.items()))))

    accepts = [
        Auth(),
        initscript_fields
        ]

    returns = Parameter(int, 'New initscript_id (> 0) if successful')


    def call(self, auth, initscript_fields):
        initscript_fields = dict(list(filter(can_update, list(initscript_fields.items()))))
        initscript = InitScript(self.api, initscript_fields)
        initscript.sync()

        self.event_objects = {'InitScript': [initscript['initscript_id']]}

        return initscript['initscript_id']
