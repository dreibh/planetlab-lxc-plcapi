#!/usr/bin/env python

from PLC.API import PLCAPI
from PLC.Faults import PLCInvalidAPIMethod
from DocBook import DocBook
import sys

api = PLCAPI(None)
methods = api.all_methods
methods.sort()
good_apis = []
bad_apis = []
for method in methods:
    try:
        good_api = api.callable(method)
        good_apis.append(good_api)
    except PLCInvalidAPIMethod, e:
        bad_apis.append((method,e))

DocBook(good_apis).Process()

if len(bad_apis):
    sys.stderr.write("UNEXPECTED: There are %d non-callable methods:\n"%(len(bad_apis)))
    for bad_api,e in bad_apis:
        sys.stderr.write("\t%s:%s\n" % (bad_api,e))
    sys.exit(-1)
