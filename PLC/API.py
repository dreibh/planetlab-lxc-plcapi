#
# PLCAPI XML-RPC and SOAP interfaces
#
# Aaron Klingaman <alk@absarokasoft.com>
# Mark Huang <mlhuang@cs.princeton.edu>
#
# Copyright (C) 2004-2006 The Trustees of Princeton University
# $Id: API.py,v 1.2 2006/09/08 19:43:31 mlhuang Exp $
#

import sys
import traceback

import xmlrpclib

import SOAPpy
from SOAPpy.Parser import parseSOAPRPC
from SOAPpy.Types import faultType
from SOAPpy.NS import NS
from SOAPpy.SOAPBuilder import buildSOAP

from PLC.Config import Config
from PLC.PostgreSQL import PostgreSQL
from PLC.Faults import *
import PLC.Methods

class PLCAPI:
    methods = PLC.Methods.methods

    def __init__(self, config = "/etc/planetlab/plc_config", encoding = "utf-8"):
        self.encoding = encoding

        # Better just be documenting the API
        if config is None:
            return

        # Load configuration
        self.config = Config(config)

        # Initialize database connection
        if self.config.PLC_DB_TYPE == "postgresql":
            self.db = PostgreSQL(self)
        else:
            raise PLCAPIError, "Unsupported database type " + config.PLC_DB_TYPE

    def callable(self, method):
        """
        Return a new instance of the specified method.
        """

        # Look up method
        if method not in self.methods:
            raise PLCInvalidAPIMethod, method

        # Get new instance of method
        try:
            classname = method.split(".")[-1]
            module = __import__("PLC.Methods." + method, globals(), locals(), [classname])
            return getattr(module, classname)(self)
        except ImportError, AttributeError:
            raise PLCInvalidAPIMethod, method

    def call(self, source, method, *args):
        """
        Call the named method from the specified source with the
        specified arguments.
        """

        function = self.callable(method)
        function.source = source
        return function(*args)

    def handle(self, source, data):
        """
        Handle an XML-RPC or SOAP request from the specified source.
        """

        # Parse request into method name and arguments
        try:
            interface = xmlrpclib
            (args, method) = xmlrpclib.loads(data)
            methodresponse = True
        except:
            interface = SOAPpy
            (r, header, body, attrs) = parseSOAPRPC(data, header = 1, body = 1, attrs = 1)
            method = r._name
            args = r._aslist()
            # XXX Support named arguments

        try:
            result = self.call(source, method, *args)
        except PLCFault, fault:
            # Handle expected faults
            if interface == xmlrpclib:
                result = fault
                methodresponse = None
            elif interface == SOAPpy:
                result = faultParameter(NS.ENV_T + ":Server", "Method Failed", method)
                result._setDetail("Fault %d: %s" % (fault.faultCode, fault.faultString))

        # Return result
        if interface == xmlrpclib:
            if not isinstance(result, PLCFault):
                result = (result,)
            data = xmlrpclib.dumps(result, methodresponse = True, encoding = self.encoding, allow_none = 1)
        elif interface == SOAPpy:
            data = buildSOAP(kw = {'%sResponse' % method: {'Result': result}}, encoding = self.encoding)

        return data
