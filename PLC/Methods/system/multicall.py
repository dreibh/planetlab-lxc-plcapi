import sys
import xmlrpc.client

from PLC.Parameter import Parameter, Mixed
from PLC.Method import Method

class multicall(Method):
    """
    Process an array of calls, and return an array of results. Calls
    should be structs of the form

    {'methodName': string, 'params': array}

    Each result will either be a single-item array containg the result
    value, or a struct of the form

    {'faultCode': int, 'faultString': string}

    This is useful when you need to make lots of small calls without
    lots of round trips.
    """

    roles = []
    accepts = [[{'methodName': Parameter(str, "Method name"),
                 'params': Parameter(list, "Method arguments")}]]
    returns = Mixed([Mixed()],
                    {'faultCode': Parameter(int, "XML-RPC fault code"),
                     'faultString': Parameter(int, "XML-RPC fault detail")})

    def __init__(self, api):
        Method.__init__(self, api)
        self.name = "system.multicall"

    def call(self, calls):
        # Some error codes, borrowed from xmlrpc-c.
        REQUEST_REFUSED_ERROR = -507

        results = []
        for call in calls:
            try:
                name = call['methodName']
                params = call['params']
                if name == 'system.multicall':
                    errmsg = "Recursive system.multicall forbidden"
                    raise xmlrpc.client.Fault(REQUEST_REFUSED_ERROR, errmsg)
                result = [self.api.call(self.source, name, *params)]
            except xmlrpc.client.Fault as fault:
                result = {'faultCode': fault.faultCode,
                          'faultString': fault.faultString}
            except:
                errmsg = "%s:%s" % (sys.exc_info()[0], sys.exc_info()[1])
                result = {'faultCode': 1, 'faultString': errmsg}
            results.append(result)
        return results
