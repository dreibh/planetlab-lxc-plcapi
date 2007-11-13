
from PLC.API import PLCAPI

def get_func_list(methods = None):
	api = PLCAPI(None)
	if not methods:
	    methods = api.methods
	return [api.callable(method) for method in methods]
