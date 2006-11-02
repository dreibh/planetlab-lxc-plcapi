#!/usr/bin/python
#
# Interactive shell for testing PLCAPI
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2005 The Trustees of Princeton University
#
# $Id: Shell.py,v 1.9 2006/10/27 15:26:44 mlhuang Exp $
#

import os, sys
import traceback
import getopt
import pydoc
import pg
import xmlrpclib
import getpass

# Append PLC to the system path
sys.path.append(os.path.dirname(os.path.realpath(sys.argv[0])))

from PLC.API import PLCAPI
from PLC.Parameter import Mixed
from PLC.Auth import Auth
from PLC.Config import Config
from PLC.Method import Method
import PLC.Methods

# Defaults
config = "/etc/planetlab/plc_config"
url = None
method = None
user = None
password = None
role = None

if not os.path.exists(sys.argv[1]):
    # Parse options if called interactively
    script = sys.argv[1]

    def usage():
        print "Usage: %s [OPTION]..." % sys.argv[0]
        print "Options:"
        print "     -f, --config=FILE       PLC configuration file"
        print "     -h, --url=URL           API URL"
        print "     -m, --method=METHOD     API authentication method"
        print "     -u, --user=EMAIL        API user name"
        print "     -p, --password=STRING   API password"
        print "     -r, --role=ROLE         API role"
        print "     -x, --xmlrpc            Use XML-RPC interface"
        print "     --help                  This message"
        sys.exit(1)

    try:
        (opts, argv) = getopt.getopt(sys.argv[1:],
                                     "f:h:m:u:p:r:x",
                                     ["config=", "cfg=", "file=",
                                      "host=",
                                      "method=",
                                      "username=", "user=",
                                      "password=", "pass=", "authstring=",
                                      "role=",
                                      "xmlrpc",
                                      "help"])
    except getopt.GetoptError, err:
        print "Error: ", err.msg
        usage()

    for (opt, optval) in opts:
        if opt == "-f" or opt == "--config" or opt == "--cfg" or opt == "--file":
            config = optval
        elif opt == "-h" or opt == "--host" or opt == "--url":
            url = optval
        elif opt == "-m" or opt == "--method":
            method = optval
        elif opt == "-u" or opt == "--username" or opt == "--user":
            user = optval
        elif opt == "-p" or opt == "--password" or opt == "--pass" or opt == "--authstring":
            password = optval
        elif opt == "-r" or opt == "--role":
            role = optval
        elif opt == "--help":
            usage()
else:
    # Do not parse options if called by a script
    opts = None

try:
    # If any XML-RPC options have been specified, do not try
    # connecting directly to the DB.
    if opts:
        raise Exception
        
    # Otherwise, first try connecting directly to the DB. If this
    # fails, try connecting to the API server via XML-RPC.
    api = PLCAPI(config)
    config = api.config
    server = None
except:
    # Try connecting to the API server via XML-RPC
    api = PLCAPI(None)
    config = Config(config)

    if url is None:
        if int(config.PLC_API_PORT) == 443:
            url = "https://"
        else:
            url = "http://"
        url += config.PLC_API_HOST + \
               ":" + str(config.PLC_API_PORT) + \
               "/" + config.PLC_API_PATH + "/"

    server = xmlrpclib.ServerProxy(url, allow_none = 1)

# Default is to use capability authentication
if (method, user, password) == (None, None, None):
    method = "capability"

if method == "capability":
    if user is None:
        user = config.PLC_API_MAINTENANCE_USER
    if password is None:
        password = config.PLC_API_MAINTENANCE_PASSWORD
    if role is None:
        role = "admin"
elif method is None:
    method = "password"

if role == "anonymous" or method == "anonymous":
    auth = {'AuthMethod': "anonymous"}
else:
    if user is None:
        print "Error: must specify a username with -u"
        usage()

    if password is None:
        try:
            password = getpass.getpass()
        except (EOFError, KeyboardInterrupt):
            print
            sys.exit(0)

    auth = {'AuthMethod': method,
            'Username': user,
            'AuthString': password}

    if role is not None:
        auth['Role'] = role

class Callable:
    """
    Wrapper to call a method either directly or remotely. Initialize
    with no arguments to use as a dummy class to support tab
    completion of API methods with dots in their names (e.g.,
    system.listMethods).
    """

    def __init__(self, method = None):
        self.name = method

        if method is not None:
            # Figure out if the function requires an authentication
            # structure as its first argument.
            self.auth = False
            
	    try:
                func = api.callable(method)
                if func.accepts and \
                   (isinstance(func.accepts[0], Auth) or \
                    (isinstance(func.accepts[0], Mixed) and \
                     filter(lambda param: isinstance(param, Auth), func.accepts[0]))):
                    self.auth = True
            except:
                traceback.print_exc()
                # XXX Ignore undefined methods for now
                pass

            if server is not None:
                self.func = getattr(server, method)
            else:
                self.func = func

    def __call__(self, *args, **kwds):
        """
        Automagically add the authentication structure if the function
        requires it and it has not been specified.
        """

        if self.auth and \
           (not args or not isinstance(args[0], dict) or \
            (not args[0].has_key('AuthMethod') and \
             not args[0].has_key('session'))):
            return self.func(auth, *args, **kwds)
        else:
            return self.func(*args, **kwds)

# Define all methods in the global namespace to support tab completion
for method in PLC.Methods.methods:
    paths = method.split(".")
    if len(paths) > 1:
        first = paths.pop(0)
        if first not in globals():
            globals()[first] = Callable()
        obj = globals()[first]
        for path in paths:
            if not hasattr(obj, path):
                if path == paths[-1]:
                    setattr(obj, path, Callable(method))
                else:
                    setattr(obj, path, Callable())
            obj = getattr(obj, path)
    else:
        globals()[method] = Callable(method)

pyhelp = help
def help(thing):
    """
    Override builtin help() function to support calling help(method).
    """

    # help(method)
    if isinstance(thing, Callable) and thing.name is not None:
        pydoc.pager(system.methodHelp(thing.name))
        return

    # help(help)
    if thing == help:
        thing = pyhelp

    # help(...)
    pyhelp(thing)

# If called by a script
if os.path.exists(sys.argv[1]):
    # Pop us off the argument stack
    sys.argv.pop(0)
    execfile(sys.argv[0])
    sys.exit(0)

# Otherwise, create an interactive shell environment

if server is None:
    print "PlanetLab Central Direct API Access"
    prompt = ""
elif auth['AuthMethod'] == "anonymous":
    prompt = "[anonymous]"
    print "Connected anonymously"
else:
    prompt = "[%s]" % auth['Username']
    print "%s connected using %s authentication" % \
          (auth['Username'], auth['AuthMethod'])
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
            except SyntaxError:
                # Fall back to executing as a statement
                exec command
        except Exception, err:
            traceback.print_exc()

except EOFError:
    print
    pass
