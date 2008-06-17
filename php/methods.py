#!/usr/bin/python
#
# Generates the PLCAPI interface for the website PHP code.
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2005 The Trustess of Princeton University
#
# $Id$
#

import os, sys
import time

from PLC.API import PLCAPI
from PLC.Method import *
from PLC.Auth import Auth

try:
    set
except NameError:
    from sets import Set
    set = Set

def php_cast(value):
    """
    Casts Python values to PHP values.
    """
    
    if value is None:
        return "NULL"
    elif isinstance(value, (list, tuple, set)):
        return "array(%s)" % ", ".join([php_cast(v) for v in value])
    elif isinstance(value, dict):
        items = ["%s => %s" % (php_cast(k), php_cast(v)) for (k, v) in value.items()]
        return "array(%s)" % ", ".join(items)
    elif isinstance(value, (int, long, bool, float)):
        return str(value)
    else:
        unicode_repr = repr(unicode(value))
        # Truncate the leading 'u' prefix
        return unicode_repr[1:]

# Class functions
api = PLCAPI(None)

api.all_methods.sort()
for method in api.all_methods:
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
            arg += " = " + php_cast(default)

        args.append(arg)

    # Write function declaration
    print "(" + ", ".join(args) + ")"

    # Begin function body
    print "{"

    # API function arguments
    i = 0
    for name, expected, default in parameters:
        # Automatically added auth structures
        if isinstance(expected, Auth) or \
           (isinstance(expected, Mixed) and \
            filter(lambda sub: isinstance(sub, Auth), expected)):
            print "  $args[] = $this->auth;"
            continue

        print " ",
        if name not in min_args:
            print "if (func_num_args() > %d)" % i, 
        print "$args[] = $%s;" % name

        i += 1

    # Call API function
    print "  return $this->call('%s', $args);" % method

    # End function body
    print "}"
    print
