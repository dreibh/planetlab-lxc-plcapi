#
# Apache mod_python interface for JSON requests
#
# Aaron Klingaman <alk@absarokasoft.com>
# Mark Huang <mlhuang@cs.princeton.edu>
#
# Copyright (C) 2004-2006 The Trustees of Princeton University
#

import sys
import traceback
import xmlrpc.client
from mod_python import apache

from PLC.Logger import logger

from PLC.API import PLCAPI
api = PLCAPI()

def handler(req):
    try:
        if req.method != "POST":
            req.content_type = "text/html"
            req.send_http_header()
            req.write("""
<html><head>
<title>PLCAPI JSON Interface</title>
</head><body>
<h1>PLCAPI JSON Interface</h1>
<p>Please POST JSON to access the PLCAPI.</p>
</body></html>
""")
            return apache.OK

        # Read request
        request = req.read(int(req.headers_in['content-length']))

        # mod_python < 3.2: The IP address portion of remote_addr is
        # incorrect (always 0.0.0.0) when IPv6 is enabled.
        # http://issues.apache.org/jira/browse/MODPYTHON-64?page=all
        (remote_ip, remote_port) = req.connection.remote_addr
        remote_addr = (req.connection.remote_ip, remote_port)

        # Handle request
        response = api.handle_json(remote_addr, request)

        # Shut down database connection, otherwise up to MaxClients DB
        # connections will remain open.
        api.db.close()

        # Write response
        req.content_type = "text/json; charset=" + api.encoding
        req.send_http_header()
        req.write(response)

        return apache.OK

    except Exception as err:
        logger.exception("INTERNAL ERROR !!")
        return apache.HTTP_INTERNAL_SERVER_ERROR
