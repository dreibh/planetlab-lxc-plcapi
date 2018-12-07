#!/usr/bin/python
#
# Sapan Bhatia <sapanb@cs.princeton.edu>
#
# Generates a WSDL for plcapi
# Current limitations:
# - Invalid for the following reasons 
# - The types are python types, not WSDL types
# - I'm not sure of what to do with the auth structure 

import os, sys
import time
import pdb
import xml.dom.minidom
import inspect
import globals

from PLC.API import PLCAPI
from PLC.Method import *
from PLC.Auth import Auth
from PLC.Parameter import Parameter, Mixed, python_type, xmlrpc_type


api = PLCAPI(None)

# Class functions

def param_type(param):
    if isinstance(param, Mixed) and len(param):
        subtypes = [param_type(subparam) for subparam in param]
        return " or ".join(subtypes)
    elif isinstance(param, (list, tuple, set)) and len(param):
        return "array of " + " or ".join([param_type(subparam) for subparam in param])
    else:
        return xmlrpc_type(python_type(param))


def add_wsdl_ports_and_bindings (wsdl):
    api.all_methods.sort()
    for method in api.all_methods:
        # Skip system. methods
        if "system." in method:
            continue

        function = api.callable(method)

        # Commented documentation
        #lines = ["// " + line.strip() for line in function.__doc__.strip().split("\n")]
        #print "\n".join(lines)
        #print

        
        in_el = wsdl.firstChild.appendChild(wsdl.createElement("wsdl:message"))
        in_el.setAttribute("name", function.name + "_in")

        # Arguments

        if (function.accepts):
            (min_args, max_args, defaults) = function.args()
            for (argname,argtype) in zip(max_args,function.accepts):
                arg_part = in_el.appendChild(wsdl.createElement("wsdl:part"))
                arg_part.setAttribute("name", argname)
                arg_part.setAttribute("type", param_type(argtype))
                
        # Return type            
        return_type = function.returns
        out_el = wsdl.firstChild.appendChild(wsdl.createElement("wsdl:message"))
        out_el.setAttribute("name", function.name + "_out")
        ret_part = out_el.appendChild(wsdl.createElement("wsdl:part"))
        ret_part.setAttribute("name", "returnvalue")
        ret_part.setAttribute("type", param_type(return_type))

        # Port connecting arguments with return type

        port_el = wsdl.firstChild.appendChild(wsdl.createElement("wsdl:portType"))
        port_el.setAttribute("name", function.name + "_port")
        
        op_el = port_el.appendChild(wsdl.createElement("wsdl:operation"))
        op_el.setAttribute("name", function.name)
        op_el.appendChild(wsdl.createElement("wsdl:input")).setAttribute("message","tns:" + function.name + "_in")
        op_el.appendChild(wsdl.createElement("wsdl:output")).setAttribute("message","tns:" + function.name + "_out")

        # Bindings

        bind_el = wsdl.firstChild.appendChild(wsdl.createElement("wsdl:binding"))
        bind_el.setAttribute("name", function.name + "_binding")
        bind_el.setAttribute("type", "tns:" + function.name + "_port")
        
        soap_bind = bind_el.appendChild(wsdl.createElement("soap:binding"))
        soap_bind.setAttribute("style", "rpc")
        soap_bind.setAttribute("transport","http://schemas.xmlsoap.org/soap/http")

        
        wsdl_op = bind_el.appendChild(wsdl.createElement("wsdl:operation"))
        wsdl_op.setAttribute("name", function.name)
        wsdl_op.appendChild(wsdl.createElement("soap:operation")).setAttribute("soapAction",
                "urn:" + function.name)

        
        wsdl_input = wsdl_op.appendChild(wsdl.createElement("wsdl:input"))
        input_soap_body = wsdl_input.appendChild(wsdl.createElement("soap:body"))
        input_soap_body.setAttribute("use", "encoded")
        input_soap_body.setAttribute("namespace", "urn:" + function.name)
        input_soap_body.setAttribute("encodingStyle","http://schemas.xmlsoap.org/soap/encoding/")

        
        wsdl_output = wsdl_op.appendChild(wsdl.createElement("wsdl:output"))
        output_soap_body = wsdl_output.appendChild(wsdl.createElement("soap:body"))
        output_soap_body.setAttribute("use", "encoded")
        output_soap_body.setAttribute("namespace", "urn:" + function.name)
        output_soap_body.setAttribute("encodingStyle","http://schemas.xmlsoap.org/soap/encoding/")
        

def add_wsdl_service(wsdl):
    service_el = wsdl.firstChild.appendChild(wsdl.createElement("wsdl:service"))
    service_el.setAttribute("name", "plc_api_service")

    for method in api.all_methods:
        name=api.callable(method).name
        servport_el = service_el.appendChild(wsdl.createElement("wsdl:port"))
        servport_el.setAttribute("name", name + "_port")
        servport_el.setAttribute("binding", "tns:" + name + "_binding")

    soapaddress = servport_el.appendChild(wsdl.createElement("soap:address"))
    soapaddress.setAttribute("location", "%s" % globals.plc_ns)


def get_wsdl_definitions():
    wsdl_text_header = """
        <wsdl:definitions
        name="auto_generated"
        targetNamespace="%s"
        xmlns:xsd="http://www.w3.org/2000/10/XMLSchema"
        xmlns:tns="xmlns:%s"
        xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
        xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"/>""" % (globals.plc_ns,globals.plc_ns)
        
    wsdl = xml.dom.minidom.parseString(wsdl_text_header)

    return wsdl
    

wsdl = get_wsdl_definitions()
add_wsdl_ports_and_bindings(wsdl)
add_wsdl_service(wsdl)


print(wsdl.toprettyxml())

