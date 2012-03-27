from PLC.Faults import *
from PLC.Method import Method
from PLC.Parameter import Parameter, Mixed
from PLC.Filter import Filter
from PLC.InitScripts import InitScript, InitScripts
from PLC.Auth import Auth

class GetInitScripts(Method):
    """
    Returns an array of structs containing details about initscripts.
    If initscript_filter is specified and is an array of initscript
    identifiers, or a struct of initscript attributes, only initscripts
    matching the filter will be returned. If return_fields is specified,
    only the specified details will be returned.
    """

    roles = ['admin', 'pi', 'user', 'tech', 'node']

    accepts = [
        Auth(),
        Mixed([Mixed(InitScript.fields['initscript_id'],
                     InitScript.fields['name'])],
              Filter(InitScript.fields)),
        Parameter([str], "List of fields to return", nullok = True)
        ]

    returns = [InitScript.fields]


    def call(self, auth, initscript_filter = None, return_fields = None):
        return InitScripts(self.api, initscript_filter, return_fields)
