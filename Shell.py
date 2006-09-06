#!/usr/bin/python
#
# Interactive shell for testing PLCAPI
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2005 The Trustees of Princeton University
#
# $Id: Shell.py,v 1.1 2006/09/06 15:33:59 mlhuang Exp $
#

import os, sys
import traceback
import getopt
import pydoc

from PLC.API import PLCAPI
from PLC.Method import Method

# Defaults
config = "/etc/planetlab/plc_config"

def usage():
    print "Usage: %s [OPTION]..." % sys.argv[0]
    print "Options:"
    print "     -f, --config=FILE       PLC configuration file (default: %s)" % config
    print "     -h, --help              This message"
    sys.exit(1)

# Get options
try:
    (opts, argv) = getopt.getopt(sys.argv[1:], "f:h", ["config=", "help"])
except getopt.GetoptError, err:
    print "Error: " + err.msg
    usage()

for (opt, optval) in opts:
    if opt == "-f" or opt == "--config":
        config = optval
    elif opt == "-h" or opt == "--help":
        usage()

api = PLCAPI(config)

auth = {'AuthMethod': "capability",
        'Username': api.config.PLC_API_MAINTENANCE_USER,
        'AuthString': api.config.PLC_API_MAINTENANCE_PASSWORD,
        'Role': "admin"}

class Dummy:
    """
    Dummy class to support tab completion of API methods with dots in
    their names (e.g., system.listMethods).
    """
    pass
        
# Define all methods in the global namespace to support tab completion
for method in api.methods:
    paths = method.split(".")
    if len(paths) > 1:
        first = paths.pop(0)
        if first not in globals():
            globals()[first] = Dummy()
        obj = globals()[first]
        for path in paths:
            if not hasattr(obj, path):
                if path == paths[-1]:
                    setattr(obj, path, api.callable(method))
                else:
                    setattr(obj, path, Dummy())
            obj = getattr(obj, path)
    else:
        globals()[method] = api.callable(method)

pyhelp = help
def help(thing):
    """
    Override builtin help() function to support calling help(method).
    """

    if isinstance(thing, Method):
        return pydoc.pager(thing.help())
    else:
        return pyhelp(thing)

# If a file is specified
if argv:
    execfile(argv[0])
    sys.exit(0)

# Otherwise, create an interactive shell environment

print "PlanetLab Central Direct API Access"
prompt = ""
print 'Type "system.listMethods()" or "help(method)" for more information.'

# Readline and tab completion support
import atexit
import readline
import rlcompleter

# Load command history
history_path = os.path.join(os.environ["HOME"], ".plcapi_history")
try:
    file(history_path, 'a').close()
    readline.read_history_file(history_path)
    atexit.register(readline.write_history_file, history_path)
except IOError:
    pass

# Enable tab completion
readline.parse_and_bind("tab: complete")

try:
    while True:
        command = ""
        while True:
            # Get line
            try:
                if command == "":
                    sep = ">>> "
                else:
                    sep = "... "
                line = raw_input(prompt + sep)
            # Ctrl-C
            except KeyboardInterrupt:
                command = ""
                print
                break

            # Build up multi-line command
            command += line

            # Blank line or first line does not end in :
            if line == "" or (command == line and line[-1] != ':'):
                break

            command += os.linesep

        # Blank line
        if command == "":
            continue
        # Quit
        elif command in ["q", "quit", "exit"]:
            break

        try:
            try:
                # Try evaluating as an expression and printing the result
                result = eval(command)
                if result is not None:
                    print result
            except:
                # Fall back to executing as a statement
                exec command
        except Exception, err:
            traceback.print_exc()

except EOFError:
    print
    pass
