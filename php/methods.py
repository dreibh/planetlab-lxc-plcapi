#!/usr/bin/python
#
# Generates the PLCAPI interface for the website PHP code.
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2005 The Trustess of Princeton University
#
# $Id: methods.py,v 1.1 2006/10/25 20:32:44 mlhuang Exp $
#

import os, sys
import time

from PLC.API import PLCAPI
from PLC.Method import *
from PLC.Auth import Auth

# Class functions
api = PLCAPI(None)

api.methods.sort()
for method in api.methods:
    # Skip system. methods
    if "system." in method:
        continue

    function = api.callable(method)

    # Commented documentation
    lines = ["// " + line.strip() for line in function.__doc__.strip().split("\n")]
    print "\n".join(lines)
    print

    # Function declaration
    print "function " + function.name,

    # PHP function arguments
    args = []
    (min_args, max_args, defaults) = function.args()
    parameters = zip(max_args, function.accepts, defaults)

    for name, expected, default in parameters:
        # Skip auth structures (added automatically)
        if isinstance(expected, Auth) or \
           (isinstance(expected, Mixed) and \
            filter(lambda sub: isinstance(sub, Auth), expected)):
            continue

        # Declare parameter
        arg = "$" + name

        # Set optional parameters to their defaults
        if name not in min_args:
            arg += " = "
            if default is None:
                arg += "NULL"
            elif isinstance(default, (list, tuple, set)):
                arg += "array(%s)" % ", ".join(default)
            elif isinstance(default, dict):
                items = ["%s => %s" % (key, value) for (key, value) in default.items()]
                arg += "array(%s)" % ", ".join(items)

        args.append(arg)

    # Write function declaration
    print "(" + ", ".join(args) + ")"

    # Begin function body
    print "{"

    # API function arguments
    for name, expected, default in parameters:
        # Automatically added auth structures
        if isinstance(expected, Auth) or \
           (isinstance(expected, Mixed) and \
            filter(lambda sub: isinstance(sub, Auth), expected)):
            print "  $args[] = $this->auth;"
            continue

        print "  $args[] = $%s;" % name

    # Call API function
    print "  return $this->call('%s', $args);" % method

    # End function body
    print "}"
    print
