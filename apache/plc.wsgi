# -*- python -*-
#
# Apache mod_wsgi python interface
#
# Copyright (C) 2004-2006 The Trustees of Princeton University
#

import sys
sys.path.append('/usr/share/plc_api')
sys.stdout = sys.stderr
import traceback
from PLC.Logger import logger
from PLC.API import PLCAPI

def application(environ, start_response):
    try:
        status = '200 OK'
        if environ.get('REQUEST_METHOD') != 'POST':
            content_type = 'text/html; charset=utf-8'
            output = """
<html><head>
<title>PLCAPI WSGI XML-RPC/SOAP Interface</title>
</head><body>
<h1>PLCAPI WSGI XML-RPC/SOAP Interface</h1>
<p>Please use XML-RPC or SOAP to access the PLCAPI.</p>
<p>At the very least you need to use a POST method.</p>
</body></html>
"""
        else:
            # Thomas Dreibholz <dreibh@simula.no>
            # Note that this function is called within multiple threads!
            # "api" MUST be a local variable instead of a global one.
            # Otherwise, this causes concurrent accesses to the same
            # object within different threads!
            api = PLCAPI()
            api.environ = environ
            content_type = 'text/xml; charset=utf-8'
            ip = environ.get('REMOTE_ADDR')
            port = environ.get('REMOTE_PORT')
            output = api.handle((ip,port),  environ.get('wsgi.input').read())
# uncomment for debug
#            try:
#                with open("/tmp/dbgplc.log", "a") as f:
#                    print(f"{ip=} {port=}\n"
#                          f"{output=}",
#                          file=f)
#            except Exception as exc:
#                pass
            # Shut down database connection, otherwise up to MaxClients DB
            # connections will remain open.
            api.db.close()
    except Exception as err:
        status = '500 Internal Server Error'
        content_type = 'text/html; charset=utf-8'
        output = 'Internal Server Error'
        logger.exception("INTERNAL ERROR !!")

    # Write response
    # with python3 wsgi expects a bytes object here
    output = output.encode()
    response_headers = [('Content-type', '%s' % content_type),
                       ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]
