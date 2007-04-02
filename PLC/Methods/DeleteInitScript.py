from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.InitScripts import InitScript, InitScripts
from PLC.Auth import Auth

class DeleteInitScript(Method):
    """
    Deletes an existing initscript.  
    
    Returns 1 if successfuli, faults otherwise. 
    """

    roles = ['admin']

    accepts = [
        Auth(),
        InitScript.fields['initscript_id']
        ]

    returns = Parameter(int, '1 if successful')
    

    def call(self, auth, initscript_id):
        initscripts = InitScripts(self.api, [initscript_id])
        if not initscripts:
            raise PLCInvalidArgument, "No such initscript"

        initscript = initscripts[0]
        initscript.delete()
	self.event_objects = {'InitScript':  [initscript['initscript_id']]}

        return 1
