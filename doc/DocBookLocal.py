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
    except PLCInvalidAPIMethod as exc:
        bad_apis.append((method, exc))

DocBook(good_apis).Process()

if bad_apis:
    sys.stderr.write("UNEXPECTED: There are %d non-callable methods:\n"
                     % (len(bad_apis)))
    for method, exc in bad_apis:
        sys.stderr.write("\tmethod=<%s> exc=%s\n" % (method, exc))
    sys.exit(-1)
