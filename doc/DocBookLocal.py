#!/usr/bin/env python

from PLC.API import PLCAPI
from DocBook import DocBook

def api_methods():
    api = PLCAPI(None)
    methods = api.methods
    return [api.callable(method) for method in methods]

DocBook(api_methods ()).Process()
