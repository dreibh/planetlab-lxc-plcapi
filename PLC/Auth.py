#
# PLCAPI authentication parameters
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#

import crypt
try:
    from hashlib import sha1 as sha
except ImportError:
    import sha
import hmac
import time
import os

from PLC.Faults import *
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Persons
from PLC.Nodes import Node, Nodes
from PLC.Interfaces import Interface, Interfaces
from PLC.Sessions import Session, Sessions
from PLC.Peers import Peer, Peers
from PLC.Keys import Keys
from PLC.Boot import notify_owners

class Auth(Parameter):
    """
    Base class for all API authentication methods, as well as a class
    that can be used to represent all supported API authentication
    methods.
    """

    def __init__(self, auth = None):
        if auth is None:
            auth = {'AuthMethod': Parameter(str, "Authentication method to use", optional = False)}
        Parameter.__init__(self, auth, "API authentication structure")

    def check(self, method, auth, *args):
        global auth_methods

        # Method.type_check() should have checked that all of the
        # mandatory fields were present.
        assert 'AuthMethod' in auth

        if auth['AuthMethod'] in auth_methods:
            expected = auth_methods[auth['AuthMethod']]()
        else:
            sm = "'" + "', '".join(auth_methods.keys()) + "'"
            raise PLCInvalidArgument("must be " + sm, "AuthMethod")

        # Re-check using the specified authentication method
        method.type_check("auth", auth, expected, (auth,) + args)

class GPGAuth(Auth):
    """
    Proposed PlanetLab federation authentication structure.
    """

    def __init__(self):
        Auth.__init__(self, {
            'AuthMethod': Parameter(str, "Authentication method to use, always 'gpg'", optional = False),
            'name': Parameter(str, "Peer or user name", optional = False),
            'signature': Parameter(str, "Message signature", optional = False)
            })

    def check(self, method, auth, *args):
        try:
            peers = Peers(method.api, [auth['name']])
            if peers:
                if 'peer' not in method.roles:
                    raise PLCAuthenticationFailure, "GPGAuth: Not allowed to call method, missing 'peer' role"

                method.caller = peer = peers[0]
                gpg_keys = [ peer['key'] ]
            else:
                persons = Persons(method.api, {'email': auth['name'], 'enabled': True, 'peer_id': None})
                if not persons:
                    raise PLCAuthenticationFailure, "GPGAuth: No such user '%s'" % auth['name']

                method.caller = person = persons[0]
                if not set(person['roles']).intersection(method.roles):
                    raise PLCAuthenticationFailure, "GPGAuth: Not allowed to call method, missing role"

                keys = Keys(method.api, {'key_id': person['key_ids'], 'key_type': "gpg", 'peer_id': None})
                gpg_keys = [ key['key'] for key in keys ]

            if not gpg_keys:
                raise PLCAuthenticationFailure, "GPGAuth: No GPG key on record for peer or user '%s'"%auth['name']

            for gpg_key in gpg_keys:
                try:
                    from PLC.GPG import gpg_verify
                    gpg_verify(args, gpg_key, auth['signature'], method.name)
                    return
                except PLCAuthenticationFailure, fault:
                    pass

            raise fault

        except PLCAuthenticationFailure, fault:
            # XXX Send e-mail
            raise fault

class SessionAuth(Auth):
    """
    Secondary authentication method. After authenticating with a
    primary authentication method, call GetSession() to generate a
    session key that may be used for subsequent calls.
    """

    def __init__(self):
        Auth.__init__(self, {
            'AuthMethod': Parameter(str, "Authentication method to use, always 'session'", optional = False),
            'session': Parameter(str, "Session key", optional = False)
            })

    def check(self, method, auth, *args):
        # Method.type_check() should have checked that all of the
        # mandatory fields were present.
        assert auth.has_key('session')

        # Get session record
        sessions = Sessions(method.api, [auth['session']], expires = None)
        if not sessions:
            raise PLCAuthenticationFailure, "SessionAuth: No such session"
        session = sessions[0]

        try:
            if session['node_id'] is not None:
                nodes = Nodes(method.api, {'node_id': session['node_id'], 'peer_id': None})
                if not nodes:
                    raise PLCAuthenticationFailure, "SessionAuth: No such node"
                node = nodes[0]

                if 'node' not in method.roles:
                    # using PermissionDenied rather than AuthenticationFailure here because
                    # if that fails we don't want to delete the session..
                    raise PLCPermissionDenied, "SessionAuth: Not allowed to call method %s, missing 'node' role"%method.name

                method.caller = node

            elif session['person_id'] is not None and session['expires'] > time.time():
                persons = Persons(method.api, {'person_id': session['person_id'], 'enabled': True, 'peer_id': None})
                if not persons:
                    raise PLCAuthenticationFailure, "SessionAuth: No such enabled account"
                person = persons[0]

                if not set(person['roles']).intersection(method.roles):
                    method_message="method %s has roles [%s]"%(method.name,','.join(method.roles))
                    person_message="caller %s has roles [%s]"%(person['email'],','.join(person['roles']))
                    # not PLCAuthenticationFailure b/c that would end the session..
                    raise PLCPermissionDenied, "SessionAuth: missing role, %s -- %s"%(method_message,person_message)

                method.caller = person

            else:
                raise PLCAuthenticationFailure, "SessionAuth: Invalid session"

        except PLCAuthenticationFailure, fault:
            session.delete()
            raise fault

class BootAuth(Auth):
    """
    PlanetLab version 3.x node authentication structure. Used by the
    Boot Manager to make authenticated calls to the API based on a
    unique node key or boot nonce value.

    The original parameter serialization code did not define the byte
    encoding of strings, or the string encoding of all other types. We
    define the byte encoding to be UTF-8, and the string encoding of
    all other types to be however Python version 2.3 unicode() encodes
    them.
    """

    def __init__(self):
        Auth.__init__(self, {
            'AuthMethod': Parameter(str, "Authentication method to use, always 'hmac'", optional = False),
            'node_id': Parameter(int, "Node identifier", optional = False),
            'value': Parameter(str, "HMAC of node key and method call", optional = False)
            })

    def canonicalize(self, args):
        values = []

        for arg in args:
            if isinstance(arg, list) or isinstance(arg, tuple):
                # The old implementation did not recursively handle
                # lists of lists. But neither did the old API itself.
                values += self.canonicalize(arg)
            elif isinstance(arg, dict):
                # Yes, the comments in the old implementation are
                # misleading. Keys of dicts are not included in the
                # hash.
                values += self.canonicalize(arg.values())
            else:
                # We use unicode() instead of str().
                values.append(unicode(arg))

        return values

    def check(self, method, auth, *args):
        # Method.type_check() should have checked that all of the
        # mandatory fields were present.
        assert auth.has_key('node_id')

        if 'node' not in method.roles:
            raise PLCAuthenticationFailure, "BootAuth: Not allowed to call method, missing 'node' role"

        try:
            nodes = Nodes(method.api, {'node_id': auth['node_id'], 'peer_id': None})
            if not nodes:
                raise PLCAuthenticationFailure, "BootAuth: No such node"
            node = nodes[0]

            # Jan 2011 : removing support for old boot CDs
            if node['key']:
                key = node['key']
            else:
                raise PLCAuthenticationFailure, "BootAuth: No node key"

            # Yes, this is the "canonicalization" method used.
            args = self.canonicalize(args)
            args.sort()
            msg = "[" + "".join(args) + "]"

            # We encode in UTF-8 before calculating the HMAC, which is
            # an 8-bit algorithm.
            # python 2.6 insists on receiving a 'str' as opposed to a 'unicode'
            digest = hmac.new(str(key), msg.encode('utf-8'), sha).hexdigest()

            if digest != auth['value']:
                raise PLCAuthenticationFailure, "BootAuth: Call could not be authenticated"

            method.caller = node

        except PLCAuthenticationFailure, fault:
            if nodes:
                notify_owners(method, node, 'authfail', include_pis = True, include_techs = True, fault = fault)
            raise fault

class AnonymousAuth(Auth):
    """
    PlanetLab version 3.x anonymous authentication structure.
    """

    def __init__(self):
        Auth.__init__(self, {
            'AuthMethod': Parameter(str, "Authentication method to use, always 'anonymous'", False),
            })

    def check(self, method, auth, *args):
        if 'anonymous' not in method.roles:
            raise PLCAuthenticationFailure, "AnonymousAuth: method cannot be called anonymously"

        method.caller = None

class PasswordAuth(Auth):
    """
    PlanetLab version 3.x password authentication structure.
    """

    def __init__(self):
        Auth.__init__(self, {
            'AuthMethod': Parameter(str, "Authentication method to use, always 'password' or 'capability'", optional = False),
            'Username': Parameter(str, "PlanetLab username, typically an e-mail address", optional = False),
            'AuthString': Parameter(str, "Authentication string, typically a password", optional = False),
            })

    def check(self, method, auth, *args):
        # Method.type_check() should have checked that all of the
        # mandatory fields were present.
        assert auth.has_key('Username')

        # Get record (must be enabled)
        persons = Persons(method.api, {'email': auth['Username'].lower(), 'enabled': True, 'peer_id': None})
        if len(persons) != 1:
            raise PLCAuthenticationFailure, "PasswordAuth: No such account"

        person = persons[0]

        if auth['Username'] == method.api.config.PLC_API_MAINTENANCE_USER:
            # "Capability" authentication, whatever the hell that was
            # supposed to mean. It really means, login as the special
            # "maintenance user" using password authentication. Can
            # only be used on particular machines (those in a list).
            sources = method.api.config.PLC_API_MAINTENANCE_SOURCES.split()
            if method.source is not None and method.source[0] not in sources:
                raise PLCAuthenticationFailure, "PasswordAuth: Not allowed to login to maintenance account"

            # Not sure why this is not stored in the DB
            password = method.api.config.PLC_API_MAINTENANCE_PASSWORD

            if auth['AuthString'] != password:
                raise PLCAuthenticationFailure, "PasswordAuth: Maintenance account password verification failed"
        else:
            # Compare encrypted plaintext against encrypted password stored in the DB
            plaintext = auth['AuthString'].encode(method.api.encoding)
            password = person['password']

            # Protect against blank passwords in the DB
            if password is None or password[:12] == "" or \
               crypt.crypt(plaintext, password[:12]) != password:
                raise PLCAuthenticationFailure, "PasswordAuth: Password verification failed"

        if not set(person['roles']).intersection(method.roles):
            method_message="method %s has roles [%s]"%(method.name,','.join(method.roles))
            person_message="caller %s has roles [%s]"%(person['email'],','.join(person['roles']))
            raise PLCAuthenticationFailure, "PasswordAuth: missing role, %s -- %s"%(method_message,person_message)

        method.caller = person

auth_methods = {'session': SessionAuth,
                'password': PasswordAuth,
                'capability': PasswordAuth,
                'gpg': GPGAuth,
                'hmac': BootAuth,
                'hmac_dummybox': BootAuth,
                'anonymous': AnonymousAuth}

path = os.path.dirname(__file__) + "/Auth.d"
try:
    extensions = os.listdir(path)
except OSError, e:
    extensions = []
for extension in extensions:
    if extension.startswith("."):
        continue
    if not extension.endswith(".py"):
        continue
    execfile("%s/%s" % (path, extension))
del extensions
