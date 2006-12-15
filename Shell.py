#!/usr/bin/python
#
# Interactive shell for testing PLCAPI
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2005 The Trustees of Princeton University
#
# $Id: Shell.py,v 1.17 2006/12/13 22:29:28 mlhuang Exp $
#

import os, sys
import traceback
import getopt
import pydoc
import pg
import xmlrpclib
import getpass

from PLC.API import PLCAPI
from PLC.Parameter import Mixed
from PLC.Auth import Auth
from PLC.Config import Config
from PLC.Method import Method
from PLC.PyCurl import PyCurlTransport
import PLC.Methods

# the list of globals formerly defined by Shell.py before it was made a class
former_globals = ['api','auth','config','begin','commit','calls']

pyhelp = help
def help(thing):
    """
    Override builtin help() function to support calling help(method).
    """

    # help(method)
    if isinstance(thing, Shell.Callable) and thing.name is not None:
        pydoc.pager(system.methodHelp(thing.name))
        return

    # help(help)
    if thing == help:
        thing = pyhelp

    # help(...)
    pyhelp(thing)

####################
class Shell:

    def __init__ (self,argv,config=None):

        # Defaults
        if config is not None:
            self.config=config
        else:
            # support running on non-myplc boxes
            default_config_file = "/etc/planetlab/plc_config"
            try:
                open (default_config_file).close()
            except:
                default_config_file="/dev/null"
            self.config = default_config_file
        self.url = None
        self.method = None
        self.user = None
        self.password = None
        self.role = None
        self.xmlrpc = False
        self.server = None
        self.cacert = None

        # More convenient multicall support
        self.multi = False
        self.calls = []
        self.argv = argv

    def init_from_argv (self):

        try:
            (opts, argv) = getopt.getopt(self.argv[1:],
                                         "f:h:m:u:p:r:x",
                                         ["config=", "cfg=", "file=",
                                          "host=","url=",
                                          "method=",
                                          "username=", "user=",
                                          "password=", "pass=", "authstring=",
                                          "role=",
                                          "xmlrpc",
                                          "cacert=",
                                          "help"])
        except getopt.GetoptError, err:
            print "Error: ", err.msg
            self.usage(self.argv)
                
        for (opt, optval) in opts:
            if opt == "-f" or opt == "--config" or opt == "--cfg" or opt == "--file":
                self.config = optval
            elif opt == "-h" or opt == "--host" or opt == "--url":
                self.url = optval
            elif opt == "-m" or opt == "--method":
                self.method = optval
            elif opt == "-u" or opt == "--username" or opt == "--user":
                self.user = optval
            elif opt == "-p" or opt == "--password" or opt == "--pass" or opt == "--authstring":
                self.password = optval
            elif opt == "-r" or opt == "--role":
                self.role = optval
            elif opt == "-x" or opt == "--xmlrpc":
                self.xmlrpc = True
            elif opt == "--cacert":
                self.cacert = optval
            elif opt == "--help":
                self.usage(self.argv)

    def usage(self,argv):
        print "Usage: %s [OPTION]..." % argv[0]
        print "Options:"
        print "     -f, --config=FILE       PLC configuration file"
        print "     -h, --url=URL           API URL"
        print "     -m, --method=METHOD     API authentication method"
        print "     -u, --user=EMAIL        API user name"
        print "     -p, --password=STRING   API password"
        print "     -r, --role=ROLE         API role"
        print "     -x, --xmlrpc            Use XML-RPC interface"
        print "     --cacert=CACERT         API SSL certificate"
        print "     --help                  This message"
        sys.exit(1)

    def init_connection(self):

        # Append PLC to the system path
        sys.path.append(os.path.dirname(os.path.realpath(self.argv[0])))

        try:
            # If any XML-RPC options have been specified, do not try
            # connecting directly to the DB.
            if (self.url, self.method, self.user, self.password, self.role, self.cacert, self.xmlrpc) != \
                   (None, None, None, None, None, None, False):
                raise Exception
        
            # Otherwise, first try connecting directly to the DB. If this
            # fails, try connecting to the API server via XML-RPC.
            self.api = PLCAPI(self.config)
            self.config = self.api.config
            self.server = None
        except:
            # Try connecting to the API server via XML-RPC
            self.api = PLCAPI(None)
            self.config = Config(self.config)

            if self.url is None:
                if int(self.config.PLC_API_PORT) == 443:
                    self.url = "https://"
                else:
                    self.url = "http://"
                self.url += self.config.PLC_API_HOST + \
                            ":" + str(self.config.PLC_API_PORT) + \
                            "/" + self.config.PLC_API_PATH + "/"

            if self.cacert is None:
                self.cacert = self.config.PLC_API_CA_SSL_CRT

            self.server = xmlrpclib.ServerProxy(self.url, PyCurlTransport(self.url, self.cacert), allow_none = 1)

        # Default is to use capability authentication
        if (self.method, self.user, self.password) == (None, None, None):
            self.method = "capability"

        if self.method == "capability":
            if self.user is None:
                self.user = self.config.PLC_API_MAINTENANCE_USER
            if self.password is None:
                self.password = self.config.PLC_API_MAINTENANCE_PASSWORD
            if self.role is None:
                self.role = "admin"
        elif self.method is None:
            self.method = "password"

        if self.role == "anonymous" or self.method == "anonymous":
            self.auth = {'AuthMethod': "anonymous"}
        else:
            if self.user is None:
                print "Error: must specify a username with -u"
                self.usage()

            if self.password is None:
                try:
                    self.password = getpass.getpass()
                except (EOFError, KeyboardInterrupt):
                    print
                    sys.exit(0)

            self.auth = {'AuthMethod': self.method,
                    'Username': self.user,
                    'AuthString': self.password}

            if self.role is not None:
                self.auth['Role'] = self.role

    def begin(self):
        if self.calls:
            raise Exception, "multicall already in progress"

        self.multi = True

    def commit(self):

        if calls:
            ret = []
            self.multi = False
            results = system.multicall(calls)
            for result in results:
                if type(result) == type({}):
                    raise xmlrpclib.Fault(item['faultCode'], item['faultString'])
                elif type(result) == type([]):
                    ret.append(result[0])
                else:
                    raise ValueError, "unexpected type in multicall result"
        else:
            ret = None

        self.calls = []
        self.multi = False

        return ret

    class Callable:
        """
        Wrapper to call a method either directly or remotely. Initialize
        with no arguments to use as a dummy class to support tab
        completion of API methods with dots in their names (e.g.,
        system.listMethods).
        """

        def __init__(self, shell, method = None):
            self.shell=shell
            self.name = method

            if method is not None:
                # Figure out if the function requires an authentication
                # structure as its first argument.
                self.auth = False
            
                try:
                    func = shell.api.callable(method)
                    if func.accepts and \
                       (isinstance(func.accepts[0], Auth) or \
                        (isinstance(func.accepts[0], Mixed) and \
                         filter(lambda param: isinstance(param, Auth), func.accepts[0]))):
                        self.auth = True
                except:
                    traceback.print_exc()
                    # XXX Ignore undefined methods for now
                    pass

                if shell.server is not None:
                    self.func = getattr(shell.server, method)
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
                args = (self.shell.auth,) + args

            if self.shell.multi:
                self.shell.calls.append({'methodName': self.name, 'params': list(args)})
                return None
            else:
                return self.func(*args, **kwds)

    def init_methods (self):
        # makes methods defined on self
        for method in PLC.Methods.methods:
            # ignore path-defined methods for now
            if "." not in method:
                setattr(self,method,Shell.Callable(self,method))

    def init_globals (self):
        # Define all methods in the global namespace to support tab completion
        for method in PLC.Methods.methods:
            paths = method.split(".")
            if len(paths) > 1:
                first = paths.pop(0)
                if first not in globals():
                    globals()[first] = Shell.Callable(self)
                obj = globals()[first]
                for path in paths:
                    if not hasattr(obj, path):
                        if path == paths[-1]:
                            setattr(obj, path, Shell.Callable(self,method))
                        else:
                            setattr(obj, path, Shell.Callable(self))
                    obj = getattr(obj, path)
            else:
                globals()[method] = Shell.Callable(self,method)
        # Other stuff to be made visible in globals()
        for slot in former_globals:
            #print 'Inserting global',slot
            globals()[slot] = getattr(self,slot)

    def run_script (self):
        # Pop us off the argument stack
        self.argv.pop(0)
        execfile(self.argv[0],globals(),globals())
        sys.exit(0)
        
    def show_config (self, verbose=False):
        if self.server is None:
            print "PlanetLab Central Direct API Access"
            self.prompt = ""
        elif self.auth['AuthMethod'] == "anonymous":
            self.prompt = "[anonymous]"
            print "Connected anonymously"
        else:
            self.prompt = "[%s]" % self.auth['Username']
            print "%s connected using %s authentication" % \
                  (self.auth['Username'], self.auth['AuthMethod'])

        if verbose:
            print 'url',self.url
            print 'server',self.server
            print 'method',self.method
            print 'user',self.user,
            print 'password',self.password
            print 'role',self.role,
            print 'xmlrpc',self.xmlrpc,
            print 'multi',self.multi,
            print 'calls',self.calls
        
    def run_interactive (self):
        # Readline and tab completion support
        import atexit
        import readline
        import rlcompleter
        
        print 'Type "system.listMethods()" or "help(method)" for more information.'
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
                        line = raw_input(self.prompt + sep)
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

    # support former behaviour
    def run (self):
        if len(self.argv) < 2 or not os.path.exists(self.argv[1]):
            # Parse options if called interactively
            self.init_from_argv()
        self.init_connection()
        self.init_globals()
        # If called by a script
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
#            self.show_config()
            self.run_script()
        else:
            self.show_config()
            self.run_interactive()

    # does not run anything, support for multi-plc, see e.g. TestPeers.py 
    def init(self):
        self.init_from_argv()
        self.init_connection()
        self.init_methods()

if __name__ == '__main__':
    Shell(sys.argv).run()
