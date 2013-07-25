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
from PLC.Debug import log
from PLC.API import PLCAPI

def application(environ, start_response):
    try:
        status = '200 OK'
        if environ.get('REQUEST_METHOD') != 'POST':
            content_type = 'text/html'
            output = """
<html><head>
<title>PLCAPI WSGI XML-RPC/SOAP Interface</title>
</head><body>
<h1>PLCAPI WSGI XML-RPC/SOAP Interface</h1>
<p>Please use XML-RPC or SOAP to access the PLCAPI.</p>
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
            content_type = 'text/xml'
            ip = environ.get('REMOTE_ADDR')
            port = environ.get('REMOTE_PORT')
            output = api.handle((ip,port),  environ.get('wsgi.input').read())
            # Shut down database connection, otherwise up to MaxClients DB
            # connections will remain open.
            api.db.close()
    except Exception, err:
        status = '500 Internal Server Error'
        content_type = 'text/html'
        output = 'Internal Server Error'
        print >> log, err, traceback.format_exc()

    # Write response
    response_headers = [('Content-type', '%s' % content_type),
                       ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output] 

