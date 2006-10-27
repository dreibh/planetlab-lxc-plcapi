#
# PLCAPI XML-RPC and SOAP interfaces
#
# Aaron Klingaman <alk@absarokasoft.com>
# Mark Huang <mlhuang@cs.princeton.edu>
#
# Copyright (C) 2004-2006 The Trustees of Princeton University
# $Id: API.py,v 1.5 2006/10/24 13:47:35 mlhuang Exp $
#

import sys
import traceback

import xmlrpclib

def dump(self, value, write):
    """
    xmlrpclib cannot marshal instances of subclasses of built-in
    types. This function overrides xmlrpclib.Marshaller.__dump so that
    any value that is an instance of one of its acceptable types is
    marshalled as that type.
    """

    try:
        # Try for an exact match first
        f = self.dispatch[type(value)]
    except KeyError:
        # Try for an isinstance() match
        for Type, f in self.dispatch.iteritems():
            if isinstance(value, Type):
                f(self, value, write)
                return
        raise TypeError, "cannot marshal %s objects" % type(value)
    else:
        f(self, value, write)        

# You can't hide from me!
xmlrpclib.Marshaller._Marshaller__dump = dump

# SOAP support is optional
try:
    import SOAPpy
    from SOAPpy.Parser import parseSOAPRPC
    from SOAPpy.Types import faultType
    from SOAPpy.NS import NS
    from SOAPpy.SOAPBuilder import buildSOAP
except ImportError:
    SOAPpy = None

from PLC.Config import Config
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
            from PLC.PostgreSQL import PostgreSQL
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
        except Exception, e:
            if SOAPpy is not None:
                interface = SOAPpy
                (r, header, body, attrs) = parseSOAPRPC(data, header = 1, body = 1, attrs = 1)
                method = r._name
                args = r._aslist()
                # XXX Support named arguments
            else:
                raise e

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
