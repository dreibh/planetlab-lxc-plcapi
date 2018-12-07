#
# PLCAPI XML-RPC and SOAP interfaces
#
# Aaron Klingaman <alk@absarokasoft.com>
# Mark Huang <mlhuang@cs.princeton.edu>
#
# Copyright (C) 2004-2006 The Trustees of Princeton University
#



import os
import string
import json

import xmlrpc.client

# See "2.2 Characters" in the XML specification:
#
# #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD]
# avoiding
# [#x7F-#x84], [#x86-#x9F], [#xFDD0-#xFDDF]

invalid_codepoints = list(range(0x0, 0x8)) + [0xB, 0xC] + list(range(0xE, 0x1F))
# broke with f24, somehow we get a unicode
# as an incoming string to be translated
str_xml_escape_table = \
    string.maketrans("".join((chr(x) for x in invalid_codepoints)),
                     "?" * len(invalid_codepoints))
# loosely inspired from
# http://stackoverflow.com/questions/1324067/
# how-do-i-get-str-translate-to-work-with-unicode-strings
unicode_xml_escape_table = \
    {invalid: "?" for invalid in invalid_codepoints}


def xmlrpclib_escape(s, replace=string.replace):
    """
    xmlrpclib does not handle invalid 7-bit control characters. This
    function augments xmlrpclib.escape, which by default only replaces
    '&', '<', and '>' with entities.
    """

    # This is the standard xmlrpclib.escape function
    s = replace(s, "&", "&amp;")
    s = replace(s, "<", "&lt;")
    s = replace(s, ">", "&gt;",)

    # Replace invalid 7-bit control characters with '?'
    if isinstance(s, str):
        return s.translate(str_xml_escape_table)
    else:
        return s.translate(unicode_xml_escape_table)


def test_xmlrpclib_escape():
    inputs = [
        # full ASCII
        "".join((chr(x) for x in range(128))),
        # likewise but as a unicode string up to 256
        "".join((chr(x) for x in range(256))),
        ]
    for input in inputs:
        print("==================== xmlrpclib_escape INPUT")
        print(type(input), '->', input)
        print("==================== xmlrpclib_escape OUTPUT")
        print(xmlrpclib_escape(input))


def xmlrpclib_dump(self, value, write):
    """
    xmlrpclib cannot marshal instances of subclasses of built-in
    types. This function overrides xmlrpclib.Marshaller.__dump so that
    any value that is an instance of one of its acceptable types is
    marshalled as that type.

    xmlrpclib also cannot handle invalid 7-bit control characters. See
    above.
    """

    # Use our escape function
    args = [self, value, write]
    if isinstance(value, str):
        args.append(xmlrpclib_escape)

    try:
        # Try for an exact match first
        f = self.dispatch[type(value)]
    except KeyError:
        # Try for an isinstance() match
        for Type, f in self.dispatch.items():
            if isinstance(value, Type):
                f(*args)
                return
        raise TypeError("cannot marshal %s objects" % type(value))
    else:
        f(*args)


# You can't hide from me!
xmlrpc.client.Marshaller._Marshaller__dump = xmlrpclib_dump

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
import PLC.Accessors


def import_deep(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


class PLCAPI:

    # flat list of method names
    native_methods = PLC.Methods.native_methods

    # other_methods_map : dict {methodname: fullpath}
    # e.g. 'Accessors' -> 'PLC.Accessors.Accessors'
    other_methods_map = {}
    for subdir in ['Accessors']:
        path = "PLC."+subdir
        # scan e.g. PLC.Accessors.__all__
        pkg = __import__(path).__dict__[subdir]
        for modulename in getattr(pkg, "__all__"):
            fullpath = path + "." + modulename
            for method in getattr(import_deep(fullpath), "methods"):
                other_methods_map[method] = fullpath

    all_methods = native_methods + list(other_methods_map.keys())

    def __init__(self, config="/etc/planetlab/plc_config",
                 encoding="utf-8"):
        self.encoding = encoding

        # Better just be documenting the API
        if config is None:
            return

        # Load configuration
        self.config = Config(config)
#        print("config has keys {}"
#              .format(vars(self.config).keys()))

        # Initialize database connection
        if self.config.PLC_DB_TYPE == "postgresql":
            from PLC.PostgreSQL import PostgreSQL
            self.db = PostgreSQL(self)
        else:
            raise PLCAPIError("Unsupported database type "
                              + self.config.PLC_DB_TYPE)

        # Aspects modify the API by injecting code before, after or
        # around method calls.
        # http://github.com/baris/pyaspects/blob/master/README
        #
        if self.config.PLC_RATELIMIT_ENABLED:
            from aspects import apply_ratelimit_aspect
            apply_ratelimit_aspect()

        if getattr(self.config, "PLC_NETCONFIG_ENABLED", False):
            from aspects.netconfigaspects import apply_netconfig_aspect
            apply_netconfig_aspect()

        # Enable Caching. Only for GetSlivers for the moment.
        # TODO: we may consider to do this in an aspect like the ones above.
        try:
            if self.config.PLC_GETSLIVERS_CACHE:
                getslivers_cache = True
        except AttributeError:
            getslivers_cache = False

        if getslivers_cache:
            os.environ['DJANGO_SETTINGS_MODULE'] = 'plc_django_settings'
            from cache_utils.decorators import cached
            from PLC.Methods.GetSlivers import GetSlivers

            @cached(7200)
            def cacheable_call(cls, auth, node_id_or_hostname):
                return cls.raw_call(auth, node_id_or_hostname)

            GetSlivers.call = cacheable_call

    def callable(self, method):
        """
        Return a new instance of the specified method.
        """
        # Look up method
        if method not in self.all_methods:
            raise PLCInvalidAPIMethod(method)

        # Get new instance of method
        try:
            classname = method.split(".")[-1]
            if method in self.native_methods:
                fullpath = "PLC.Methods." + method
            else:
                fullpath = self.other_methods_map[method]
            module = __import__(fullpath, globals(), locals(), [classname])
            return getattr(module, classname)(self)
        except (ImportError, AttributeError):
            raise PLCInvalidAPIMethod("import error %s for %s"
                                      % (AttributeError, fullpath))

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
            (args, method) = xmlrpc.client.loads(data)
            methodresponse = True
        except Exception as exc:
            if SOAPpy is not None:
                interface = SOAPpy
                (r, header, body, attrs) = \
                    parseSOAPRPC(data, header=1, body=1, attrs=1)
                method = r._name
                args = r._aslist()
                # XXX Support named arguments
            else:
                raise exc

        try:
            result = self.call(source, method, *args)
        except PLCFault as fault:
            # Handle expected faults
            if interface == xmlrpclib:
                result = fault
                methodresponse = None
            elif interface == SOAPpy:
                result = faultParameter(NS.ENV_T + ":Server",
                                        "Method Failed", method)
                result._setDetail("Fault %d: %s"
                                  % (fault.faultCode, fault.faultString))

        # Return result
        if interface == xmlrpclib:
            if not isinstance(result, PLCFault):
                result = (result,)
            data = xmlrpc.client.dumps(result, methodresponse=True,
                                   encoding=self.encoding, allow_none=1)
        elif interface == SOAPpy:
            data = buildSOAP(
                kw={'%sResponse' % method: {'Result': result}},
                encoding=self.encoding)

        return data

    def handle_json(self, source, data):
        """
        Handle a JSON request
        """
        method, args = json.loads(data)
        try:
            result = self.call(source, method, *args)
        except Exception as exc:
            result = str(exc)

        return json.dumps(result)

# one simple unit test
if __name__ == '__main__':
    test_xmlrpclib_escape()
