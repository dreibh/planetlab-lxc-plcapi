#
# Replacement for xmlrpclib.SafeTransport, which does not validate
# SSL certificates. Requires PyCurl.
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#

import os
import xmlrpclib
import pycurl
from tempfile import NamedTemporaryFile

class PyCurlTransport(xmlrpclib.Transport):
    def __init__(self, uri, cert = None, timeout = 300):
        if hasattr(xmlrpclib.Transport,'__init__'):
            xmlrpclib.Transport.__init__(self)
        self.curl = pycurl.Curl()

        # Suppress signals
        self.curl.setopt(pycurl.NOSIGNAL, 1)

        # Follow redirections
        self.curl.setopt(pycurl.FOLLOWLOCATION, 1)

        # Set URL
        self.url = uri
        self.curl.setopt(pycurl.URL, str(uri))

        # Set certificate path
        if cert is not None:
            if os.path.exists(cert):
                cert_path = str(cert)
            else:
                # Keep a reference so that it does not get deleted
                self.cert = NamedTemporaryFile(prefix = "cert")
                self.cert.write(cert)
                self.cert.flush()
                cert_path = self.cert.name
            self.curl.setopt(pycurl.CAINFO, cert_path)
            self.curl.setopt(pycurl.SSL_VERIFYPEER, 2)

        # Set connection timeout
        if timeout:
            self.curl.setopt(pycurl.CONNECTTIMEOUT, timeout)
            self.curl.setopt(pycurl.TIMEOUT, timeout)

        # Set request callback
        self.body = ""
        def body(buf):
            self.body += buf
        self.curl.setopt(pycurl.WRITEFUNCTION, body)

    def request(self, host, handler, request_body, verbose = 1):
        # Set verbosity
        self.curl.setopt(pycurl.VERBOSE, verbose)

        # Post request
        self.curl.setopt(pycurl.POST, 1)
        self.curl.setopt(pycurl.POSTFIELDS, request_body)

        try:
            self.curl.perform()
            errcode = self.curl.getinfo(pycurl.HTTP_CODE)
            response = self.body
            self.body = ""
            errmsg="<no known errmsg>"
        except pycurl.error, err:
            (errcode, errmsg) = err

        if errcode == 60:
            raise Exception, "PyCurl: SSL certificate validation failed"
        elif errcode != 200:
            raise Exception, "PyCurl: HTTP error %d -- %r" % (errcode,errmsg)

        # Parse response
        p, u = self.getparser()
        p.feed(response)
        p.close()

        return u.close()
