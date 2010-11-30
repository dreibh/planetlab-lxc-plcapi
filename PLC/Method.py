#
# Base class for all PLCAPI functions
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
import xmlrpclib
from types import *
import textwrap
import os
import time
import pprint

from types import StringTypes

from PLC.Faults import *
from PLC.Parameter import Parameter, Mixed, python_type, xmlrpc_type
from PLC.Auth import Auth
from PLC.Debug import profile, log
from PLC.Events import Event, Events
from PLC.Nodes import Node, Nodes
from PLC.Persons import Person, Persons

# we inherit object because we use new-style classes for legacy methods
class Method (object):
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

    def __init__(self, api,caller=None):
        self.name = self.__class__.__name__
        self.api = api

        if caller: 
            # let a method call another one by propagating its caller
            self.caller=caller
        else:
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

            # legacy code cannot be type-checked, due to the way Method.args() works
            # as of 5.0-rc16 we don't use skip_type_check anymore
            if not hasattr(self,"skip_type_check"):
                (min_args, max_args, defaults) = self.args()

                # Check that the right number of arguments were passed in
                if len(args) < len(min_args) or len(args) > len(max_args):
                    raise PLCInvalidArgumentCount(len(args), len(min_args), len(max_args))

                for name, value, expected in zip(max_args, args, self.accepts):
                    self.type_check(name, value, expected, args)

            result = self.call(*args, **kwds)
            runtime = time.time() - start

            if self.api.config.PLC_API_DEBUG or hasattr(self, 'message'):
                self.log(None, runtime, *args)

            return result

        except PLCFault, fault:

            caller = ""
            if isinstance(self.caller, Person):
                caller = 'person_id %s'  % self.caller['person_id']
            elif isinstance(self.caller, Node):
                caller = 'node_id %s'  % self.caller['node_id']

            # Prepend caller and method name to expected faults
            fault.faultString = caller + ": " +  self.name + ": " + fault.faultString
            runtime = time.time() - start

            if self.api.config.PLC_API_DEBUG:
                self.log(fault, runtime, *args)

            raise fault

    def log(self, fault, runtime, *args):
        """
        Log the transaction
        """

        # Do not log system or Get calls
        #if self.name.startswith('system') or self.name.startswith('Get'):
        #    return False
        # Do not log ReportRunlevel
        if self.name.startswith('system'):
            return False
        if self.name.startswith('ReportRunlevel'):
            return False

        # Create a new event
        event = Event(self.api)
        event['fault_code'] = 0
        if fault:
            event['fault_code'] = fault.faultCode
        event['runtime'] = runtime

        # Redact passwords and sessions
        newargs = args
        if args:
            newargs = []
            for arg in args:
                if not isinstance(arg, dict):
                    newargs.append(arg)
                    continue
                # what type of auth this is
                if arg.has_key('AuthMethod'):
                    auth_methods = ['session', 'password', 'capability', 'gpg', 'hmac','anonymous']
                    auth_method = arg['AuthMethod']
                    if auth_method in auth_methods:
                        event['auth_type'] = auth_method
                for password in 'AuthString', 'session', 'password':
                    if arg.has_key(password):
                        arg = arg.copy()
                        arg[password] = "Removed by API"
                newargs.append(arg)

        # Log call representation
        # XXX Truncate to avoid DoS
        event['call'] = self.name + pprint.saferepr(newargs)
        event['call_name'] = self.name

        # Both users and nodes can call some methods
        if isinstance(self.caller, Person):
            event['person_id'] = self.caller['person_id']
        elif isinstance(self.caller, Node):
            event['node_id'] = self.caller['node_id']

        event.sync(commit = False)

        if hasattr(self, 'event_objects') and isinstance(self.event_objects, dict):
            for key in self.event_objects.keys():
                for object_id in self.event_objects[key]:
                    event.add_object(key, object_id, commit = False)


        # Set the message for this event
        if fault:
            event['message'] = fault.faultString
        elif hasattr(self, 'message'):
            event['message'] = self.message

        # Commit
        event.sync()

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
            elif isinstance(param, (list, tuple, set)):
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
            raise fault

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
        elif expected_type in (list, tuple, set):
            if min is not None and len(value) < min:
                raise PLCInvalidArgument, "%s must contain at least %d items" % (name, min)
            if max is not None and len(value) > max:
                raise PLCInvalidArgument, "%s must contain at most %d items" % (name, max)
        else:
            if min is not None and value < min:
                raise PLCInvalidArgument, "%s must be > %s" % (name, str(min))
            if max is not None and value > max:
                raise PLCInvalidArgument, "%s must be < %s" % (name, str(max))

        # If a list with particular types of items is expected
        if isinstance(expected, (list, tuple, set)):
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
