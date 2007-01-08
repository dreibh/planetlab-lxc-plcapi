#
# Python "binding" for GPG. I'll write GPGME bindings eventually. The
# intent is to use GPG to sign method calls, as a way of identifying
# and authenticating peers. Calls should still go over an encrypted
# transport such as HTTPS, with certificate checking.
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: GPG.py,v 1.2 2007/01/05 18:50:40 mlhuang Exp $
#

import xmlrpclib
import shutil
from StringIO import StringIO
from xml.dom import minidom
from xml.dom.ext import Canonicalize
from subprocess import Popen, PIPE, call
from tempfile import NamedTemporaryFile, mkdtemp

from PLC.Faults import *

def canonicalize(methodname, args):
    """
    Returns a canonicalized XML-RPC representation of the
    specified method call.
    """

    xml = xmlrpclib.dumps(args, methodname, encoding = 'utf-8', allow_none = 1)
    dom = minidom.parseString(xml)

    # Canonicalize(), though it claims to, does not encode unicode
    # nodes to UTF-8 properly and throws an exception unless you write
    # the stream to a file object, so just encode it ourselves.
    buf = StringIO()
    Canonicalize(dom, output = buf)
    xml = buf.getvalue().encode('utf-8')

    return xml

def gpg_sign(methodname, args, secret_keyring, keyring):
    """
    Signs the specified method call using the specified keyring files.
    """

    message = canonicalize(methodname, args)

    homedir = mkdtemp()
    p = Popen(["gpg", "--batch", "--no-tty",
               "--homedir", homedir,
               "--no-default-keyring",
               "--secret-keyring", secret_keyring,
               "--keyring", keyring,
               "--detach-sign", "--armor"],
              stdin = PIPE, stdout = PIPE, stderr = PIPE)
    p.stdin.write(message)
    p.stdin.close()
    signature = p.stdout.read()
    err = p.stderr.read()
    rc = p.wait()

    # Clean up
    shutil.rmtree(homedir)

    if rc:
        raise PLCAuthenticationFailure, "GPG signing failed with return code %d: %s" % (rc, err)

    return signature

def gpg_verify(methodname, args, signature, key):
    """
    Verifys the signature of the method call using the specified public
    key material.
    """

    message = canonicalize(methodname, args)

    # Write public key to temporary file
    keyfile = NamedTemporaryFile(suffix = '.pub')
    keyfile.write(key)
    keyfile.flush()

    # Import public key into temporary keyring
    homedir = mkdtemp()
    call(["gpg", "--batch", "--no-tty", "--homedir", homedir, "--import", keyfile.name],
         stdin = PIPE, stdout = PIPE, stderr = PIPE)

    # Write detached signature to temporary file
    sigfile = NamedTemporaryFile()
    sigfile.write(signature)
    sigfile.flush()

    # Verify signature
    p = Popen(["gpg", "--batch", "--no-tty", "--homedir", homedir, "--verify", sigfile.name, "-"],
              stdin = PIPE, stdout = PIPE, stderr = PIPE)
    p.stdin.write(message)
    p.stdin.close()
    rc = p.wait()

    # Clean up
    sigfile.close()
    shutil.rmtree(homedir)
    keyfile.close()

    if rc:
        raise PLCAuthenticationFailure, "GPG verification failed with return code %d" % rc
