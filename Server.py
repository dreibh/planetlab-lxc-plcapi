#!/usr/bin/python
#
# Simple standalone HTTP server for testing PLCAPI
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#

import os
import sys
import getopt
import traceback
import http.server

# Append PLC to the system path
sys.path.append(os.path.dirname(os.path.realpath(sys.argv[0])))

from PLC.API import PLCAPI

class PLCAPIRequestHandler(http.server.BaseHTTPRequestHandler):
    """
    Simple standalone HTTP request handler for testing PLCAPI.
    """

    def do_POST(self):
        try:
            # Read request
            request = self.rfile.read(int(self.headers["Content-length"]))

            # Handle request
            response = self.server.api.handle(self.client_address, request)

            # Write response
            self.send_response(200)
            self.send_header("Content-type", "text/xml")
            self.send_header("Content-length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

            self.wfile.flush()
            self.connection.shutdown(1)

        except Exception as e:
            # Log error
            sys.stderr.write(traceback.format_exc())
            sys.stderr.flush()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", 'text/html')
        self.end_headers()
        self.wfile.write("""
<html><head>
<title>PLCAPI XML-RPC/SOAP Interface</title>
</head><body>
<h1>PLCAPI XML-RPC/SOAP Interface</h1>
<p>Please use XML-RPC or SOAP to access the PLCAPI.</p>
</body></html>
""")        
        
class PLCAPIServer(http.server.HTTPServer):
    """
    Simple standalone HTTP server for testing PLCAPI.
    """

    def __init__(self, addr, config):
        self.api = PLCAPI(config)
        self.allow_reuse_address = 1
        http.server.HTTPServer.__init__(self, addr, PLCAPIRequestHandler)

# Defaults
addr = "0.0.0.0"
port = 8000
config = "/etc/planetlab/plc_config"

def usage():
    print("Usage: %s [OPTION]..." % sys.argv[0])
    print("Options:")
    print("     -p PORT, --port=PORT    TCP port number to listen on (default: %d)" % port)
    print("     -f FILE, --config=FILE  PLC configuration file (default: %s)" % config)
    print("     -h, --help              This message")
    sys.exit(1)

# Get options
try:
    (opts, argv) = getopt.getopt(sys.argv[1:], "p:f:h", ["port=", "config=", "help"])
except getopt.GetoptError as err:
    print("Error: " + err.msg)
    usage()

for (opt, optval) in opts:
    if opt == "-p" or opt == "--port":
        try:
            port = int(optval)
        except ValueError:
            usage()
    elif opt == "-f" or opt == "--config":
        config = optval
    elif opt == "-h" or opt == "--help":
        usage()

# Start server
PLCAPIServer((addr, port), config).serve_forever()
