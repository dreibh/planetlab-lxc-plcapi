#
# PLCAPI authentication parameters
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id$
#

import crypt

from PLC.Faults import *
from PLC.Parameter import Parameter, Mixed
from PLC.Persons import Persons

class Auth(Parameter, dict):
    """
    Base class for all API authentication methods.
    """

    def __init__(self, auth):
        Parameter.__init__(self, auth, "API authentication structure", False)
        dict.__init__(auth)

class NodeAuth(Auth):
    """
    PlanetLab version 3.x node authentication structure. Used by the
    Boot Manager to make authenticated calls to the API based on a
    unique node key or boot nonce value.
    """

    def __init__(self):
        Auth.__init__(self, {
            'AuthMethod': Parameter(str, "Authentication method to use, always 'hmac'", False),
            'node_id': Parameter(str, "Node identifier", False),
            'node_ip': Parameter(str, "Node primary IP address", False),
            'value': Parameter(str, "HMAC of node key and method call", False)
            })

    def check(self, method, auth, *args):
        # XXX Do HMAC checking
        return True

class AnonymousAuth(Auth):
    """
    PlanetLab version 3.x anonymous authentication structure.
    """

    def __init__(self):
        Auth.__init__(self, {
            'AuthMethod': Parameter(str, "Authentication method to use, always 'anonymous'", False),
            })

    def check(self, method, auth, *args):
        # Sure, dude, whatever
        return True

class PasswordAuth(Auth):
    """
    PlanetLab version 3.x password authentication structure.
    """

    def __init__(self):
        Auth.__init__(self, {
            'AuthMethod': Parameter(str, "Authentication method to use, typically 'password'", False),
            'Username': Parameter(str, "PlanetLab username, typically an e-mail address", False),
            'AuthString': Parameter(str, "Authentication string, typically a password", False),
            'Role': Parameter(str, "Role to use for this call", False)
            })

    def check(self, method, auth, *args):
        # Method.type_check() should have checked that all of the
        # mandatory fields were present.
        assert auth.has_key('Username')

        # Get record (must be enabled)
        persons = Persons(method.api, [auth['Username']], enabled = True)
        if len(persons) != 1:
            raise PLCAuthenticationFailure, "No such account"

        person = persons.values()[0]

        if auth['Username'] == method.api.config.PLC_API_MAINTENANCE_USER:
            # "Capability" authentication, whatever the hell that was
            # supposed to mean. It really means, login as the special
            # "maintenance user" using password authentication. Can
            # only be used on particular machines (those in a list).
            sources = method.api.config.PLC_API_MAINTENANCE_SOURCES.split()
            if method.source is not None and method.source[0] not in sources:
                raise PLCAuthenticationFailure, "Not allowed to login to maintenance account"

            # Not sure why this is not stored in the DB
            password = method.api.config.PLC_API_MAINTENANCE_PASSWORD

            if auth['AuthString'] != password:
                raise PLCAuthenticationFailure, "Maintenance account password verification failed"
        else:
            # Get encrypted password stored in the DB
            password = person['password']

            # Protect against blank passwords in the DB
            if password is None or password[:12] == "" or \
               crypt.crypt(auth['AuthString'], password[:12]) != password:
                raise PLCAuthenticationFailure, "Password verification failed"

        if auth['Role'] not in person['roles']:
            raise PLCAuthenticationFailure, "Account does not have " + auth['Role'] + " role"

        if method.roles and auth['Role'] not in method.roles:
            raise PLCAuthenticationFailure, "Cannot call with " + auth['Role'] + "role"

        method.caller = person
