
from PLC.API import PLCAPI


def get_func_list():
	api = PLCAPI(None)
	return [api.callable(method) for method in api.methods]
