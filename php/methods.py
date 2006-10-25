#!/usr/bin/python
#
# Generates the PLCAPI interface for the website PHP code.
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2005 The Trustess of Princeton University
#
# $Id: gen_php_api.py,v 1.13 2006/03/23 04:29:08 mlhuang Exp $
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

        # Set optional parameters to special value NULL
        if name not in min_args:
            arg += " = NULL"

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

        if name in min_args:
            print "  $args[] = $%s;" % name
        else:
            print "  if ($%s !== NULL) { $args[] = $%s; }" % (name, name)

    # Call API function
    print "  return $this->call('%s', $args);" % method

    # End function body
    print "}"
    print
