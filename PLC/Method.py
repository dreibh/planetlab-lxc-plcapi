#
# Base class for all PLCAPI functions
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: Method.py,v 1.14 2006/10/31 21:47:21 mlhuang Exp $
#

import xmlrpclib
from types import *
import textwrap
import os
import time
import pprint

from PLC.Faults import *
from PLC.Parameter import Parameter, Mixed
from PLC.Auth import Auth
from PLC.Debug import profile, log
from PLC.Events import Event, Events
from PLC.Nodes import Node, Nodes
from PLC.Persons import Person, Persons

class Method:
    """
    Base class for all PLCAPI functions. At a minimum, all PLCAPI
    functions must define:

    roles = [list of roles]
    accepts = [Parameter(arg1_type, arg1_doc), Parameter(arg2_type, arg2_doc), ...]
    returns = Parameter(return_type, return_doc)
    call(arg1, arg2, ...): method body

    Argument types may be Python types (e.g., int, bool, etc.), typed
    values (e.g., 1, True, etc.), a Parameter, or lists or
    dictionaries of possibly mixed types, values, and/or Parameters
    (e.g., [int, bool, ...]  or {'arg1': int, 'arg2': bool}).

    Once function decorators in Python 2.4 are fully supported,
    consider wrapping calls with accepts() and returns() functions
    instead of performing type checking manually.
    """

    # Defaults. Could implement authentication and type checking with
    # decorators, but they are not supported in Python 2.3 and it
    # would be hard to generate documentation without writing a code
    # parser.

    roles = []
    accepts = []
    returns = bool
    status = "current"

    def call(self, *args):
        """
        Method body for all PLCAPI functions. Must override.
        """

        return True

    def __init__(self, api):
        self.name = self.__class__.__name__
        self.api = api

        # Auth may set this to a Person instance (if an anonymous
        # method, will remain None).
        self.caller = None

        # API may set this to a (addr, port) tuple if known
        self.source = None
    	
    def __call__(self, *args, **kwds):
        """
        Main entry point for all PLCAPI functions. Type checks
        arguments, authenticates, and executes call().
        """

        try:
	    start = time.time()
            (min_args, max_args, defaults) = self.args()
	        		
	    # Check that the right number of arguments were passed in
            if len(args) < len(min_args) or len(args) > len(max_args):
                raise PLCInvalidArgumentCount(len(args), len(min_args), len(max_args))

            for name, value, expected in zip(max_args, args, self.accepts):
                self.type_check(name, value, expected, args)
	
	    result = self.call(*args, **kwds)
	    runtime = time.time() - start

            if self.api.config.PLC_API_DEBUG:
		self.log(0, runtime, *args)
	    	
	    return result

        except PLCFault, fault:
            # Prepend method name to expected faults
            fault.faultString = self.name + ": " + fault.faultString
	    runtime = time.time() - start
	    self.log(fault.faultCode, runtime, *args)
            raise fault

    def log(self, fault_code, runtime, *args):
        """
        Log the transaction 
        """	

	# Do not log system or Get calls
        if self.name.startswith('system') or self.name.startswith('Get'):
            return False

        # Create a new event
        event = Event(self.api)
        event['fault_code'] = fault_code
        event['runtime'] = runtime

        # Redact passwords and sessions
        if args and isinstance(args[0], dict):
            for password in 'AuthString', 'session':
                if args[0].has_key(password):
                    auth = args[0].copy()
                    auth[password] = "Removed by API"
                    args = (auth,) + args[1:]

        # Log call representation
        # XXX Truncate to avoid DoS
        event['call'] = self.name + pprint.saferepr(args)

        # Both users and nodes can call some methods
        if isinstance(self.caller, Person):
            event['person_id'] = self.caller['person_id']
        elif isinstance(self.caller, Node):
            event['node_id'] = self.caller['node_id']

        event.sync(commit = False)

        # XXX object_ids is currently defined as a class variable
        if hasattr(self, 'object_ids'):
            for object_id in self.object_ids:
                event.add_object(object_id, commit = False)

        # Commit
        event.sync(commit = True)

    def help(self, indent = "  "):
        """
        Text documentation for the method.
        """

        (min_args, max_args, defaults) = self.args()

        text = "%s(%s) -> %s\n\n" % (self.name, ", ".join(max_args), xmlrpc_type(self.returns))

        text += "Description:\n\n"
        lines = [indent + line.strip() for line in self.__doc__.strip().split("\n")]
        text += "\n".join(lines) + "\n\n"

        text += "Allowed Roles:\n\n"
        if not self.roles:
            roles = ["any"]
        else:
            roles = self.roles
        text += indent + ", ".join(roles) + "\n\n"

        def param_text(name, param, indent, step):
            """
            Format a method parameter.
            """

            text = indent

            # Print parameter name
            if name:
                param_offset = 32
                text += name.ljust(param_offset - len(indent))
            else:
                param_offset = len(indent)

            # Print parameter type
            param_type = python_type(param)
            text += xmlrpc_type(param_type) + "\n"

            # Print parameter documentation right below type
            if isinstance(param, Parameter):
                wrapper = textwrap.TextWrapper(width = 70,
                                               initial_indent = " " * param_offset,
                                               subsequent_indent = " " * param_offset)
                text += "\n".join(wrapper.wrap(param.doc)) + "\n"
                param = param.type

            text += "\n"

            # Indent struct fields and mixed types
            if isinstance(param, dict):
                for name, subparam in param.iteritems():
                    text += param_text(name, subparam, indent + step, step)
            elif isinstance(param, Mixed):
                for subparam in param:
                    text += param_text(name, subparam, indent + step, step)
            elif isinstance(param, (list, tuple)):
                for subparam in param:
                    text += param_text("", subparam, indent + step, step)

            return text

        text += "Parameters:\n\n"
        for name, param in zip(max_args, self.accepts):
            text += param_text(name, param, indent, indent)

        text += "Returns:\n\n"
        text += param_text("", self.returns, indent, indent)

        return text

    def args(self):
        """
        Returns a tuple:

        ((arg1_name, arg2_name, ...),
         (arg1_name, arg2_name, ..., optional1_name, optional2_name, ...),
         (None, None, ..., optional1_default, optional2_default, ...))

        That represents the minimum and maximum sets of arguments that
        this function accepts and the defaults for the optional arguments.
        """

        # Inspect call. Remove self from the argument list.
        max_args = self.call.func_code.co_varnames[1:self.call.func_code.co_argcount]
        defaults = self.call.func_defaults
        if defaults is None:
            defaults = ()

        min_args = max_args[0:len(max_args) - len(defaults)]
        defaults = tuple([None for arg in min_args]) + defaults
        
        return (min_args, max_args, defaults)

    def type_check(self, name, value, expected, args):
        """
        Checks the type of the named value against the expected type,
        which may be a Python type, a typed value, a Parameter, a
        Mixed type, or a list or dictionary of possibly mixed types,
        values, Parameters, or Mixed types.
        
        Extraneous members of lists must be of the same type as the
        last specified type. For example, if the expected argument
        type is [int, bool], then [1, False] and [14, True, False,
        True] are valid, but [1], [False, 1] and [14, True, 1] are
        not.

        Extraneous members of dictionaries are ignored.
        """

        # If any of a number of types is acceptable
        if isinstance(expected, Mixed):
            for item in expected:
                try:
                    self.type_check(name, value, item, args)
                    return
                except PLCInvalidArgument, fault:
                    pass
            xmlrpc_types = [xmlrpc_type(item) for item in expected]
            raise PLCInvalidArgument("expected %s, got %s" % \
                                     (" or ".join(xmlrpc_types),
                                      xmlrpc_type(type(value))),
                                     name)

        # If an authentication structure is expected, save it and
        # authenticate after basic type checking is done.
        if isinstance(expected, Auth):
            auth = expected
        else:
            auth = None

        # Get actual expected type from within the Parameter structure
        if isinstance(expected, Parameter):
            min = expected.min
            max = expected.max
            nullok = expected.nullok
            expected = expected.type
        else:
            min = None
            max = None
            nullok = False

        expected_type = python_type(expected)

        # If value can be NULL
        if value is None and nullok:
            return

        # Strings are a special case. Accept either unicode or str
        # types if a string is expected.
        if expected_type in StringTypes and isinstance(value, StringTypes):
            pass

        # Integers and long integers are also special types. Accept
        # either int or long types if an int or long is expected.
        elif expected_type in (IntType, LongType) and isinstance(value, (IntType, LongType)):
            pass

        elif not isinstance(value, expected_type):
            raise PLCInvalidArgument("expected %s, got %s" % \
                                     (xmlrpc_type(expected_type),
                                      xmlrpc_type(type(value))),
                                     name)

        # If a minimum or maximum (length, value) has been specified
        if expected_type in StringTypes:
            if min is not None and \
               len(value.encode(self.api.encoding)) < min:
                raise PLCInvalidArgument, "%s must be at least %d bytes long" % (name, min)
            if max is not None and \
               len(value.encode(self.api.encoding)) > max:
                raise PLCInvalidArgument, "%s must be at most %d bytes long" % (name, max)
        else:
            if min is not None and value < min:
                raise PLCInvalidArgument, "%s must be > %s" % (name, str(min))
            if max is not None and value > max:
                raise PLCInvalidArgument, "%s must be < %s" % (name, str(max))

        # If a list with particular types of items is expected
        if isinstance(expected, (list, tuple)):
            for i in range(len(value)):
                if i >= len(expected):
                    j = len(expected) - 1
                else:
                    j = i
                self.type_check(name + "[]", value[i], expected[j], args)

        # If a struct with particular (or required) types of items is
        # expected.
        elif isinstance(expected, dict):
            for key in value.keys():
                if key in expected:
                    self.type_check(name + "['%s']" % key, value[key], expected[key], args)
            for key, subparam in expected.iteritems():
                if isinstance(subparam, Parameter) and \
                   subparam.optional is not None and \
                   not subparam.optional and key not in value.keys():
                    raise PLCInvalidArgument("'%s' not specified" % key, name)

        if auth is not None:
            auth.check(self, *args)

def python_type(arg):
    """
    Returns the Python type of the specified argument, which may be a
    Python type, a typed value, or a Parameter.
    """

    if isinstance(arg, Parameter):
        arg = arg.type

    if isinstance(arg, type):
        return arg
    else:
        return type(arg)

def xmlrpc_type(arg):
    """
    Returns the XML-RPC type of the specified argument, which may be a
    Python type, a typed value, or a Parameter.
    """

    arg_type = python_type(arg)

    if arg_type == NoneType:
        return "nil"
    elif arg_type == IntType or arg_type == LongType:
        return "int"
    elif arg_type == bool:
        return "boolean"
    elif arg_type == FloatType:
        return "double"
    elif arg_type in StringTypes:
        return "string"
    elif arg_type == ListType or arg_type == TupleType:
        return "array"
    elif arg_type == DictType:
        return "struct"
    elif arg_type == Mixed:
        # Not really an XML-RPC type but return "mixed" for
        # documentation purposes.
        return "mixed"
    else:
        raise PLCAPIError, "XML-RPC cannot marshal %s objects" % arg_type
