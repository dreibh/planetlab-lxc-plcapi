#
# Python "binding" for GPG. I'll write GPGME bindings eventually. The
# intent is to use GPG to sign method calls, as a way of identifying
# and authenticating peers. Calls should still go over an encrypted
# transport such as HTTPS, with certificate checking.
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#

import os
import xmlrpclib
import shutil
from types import StringTypes
from StringIO import StringIO
from xml.dom import minidom
from xml.dom.ext import Canonicalize
from subprocess import Popen, PIPE, call
from tempfile import NamedTemporaryFile, mkdtemp

from PLC.Faults import *

def canonicalize(args, methodname = None, methodresponse = False):
    """
    Returns a canonicalized XML-RPC representation of the specified
    method call (methodname != None) or response (methodresponse =
    True).
    """

    xml = xmlrpclib.dumps(args, methodname, methodresponse, encoding = 'utf-8', allow_none = 1)
    dom = minidom.parseString(xml)

    # Canonicalize(), though it claims to, does not encode unicode
    # nodes to UTF-8 properly and throws an exception unless you write
    # the stream to a file object, so just encode it ourselves.
    buf = StringIO()
    Canonicalize(dom, output = buf)
    xml = buf.getvalue().encode('utf-8')

    return xml

def gpg_export(keyring, armor = True):
    """
    Exports the specified public keyring file.
    """

    homedir = mkdtemp()
    args = ["gpg", "--batch", "--no-tty",
            "--homedir", homedir,
            "--no-default-keyring",
            "--keyring", keyring,
            "--export"]
    if armor:
        args.append("--armor")

    p = Popen(args, stdin = PIPE, stdout = PIPE, stderr = PIPE, close_fds = True)
    export = p.stdout.read()
    err = p.stderr.read()
    rc = p.wait()

    # Clean up
    shutil.rmtree(homedir)

    if rc:
        raise PLCAuthenticationFailure, "GPG export failed with return code %d: %s" % (rc, err)

    return export

def gpg_sign(args, secret_keyring, keyring, methodname = None, methodresponse = False, detach_sign = True):
    """
    Signs the specified method call (methodname != None) or response
    (methodresponse == True) using the specified GPG keyring files. If
    args is not a tuple representing the arguments to the method call
    or the method response value, then it should be a string
    representing a generic message to sign (detach_sign == True) or
    sign/encrypt (detach_sign == False) specified). Returns the
    detached signature (detach_sign == True) or signed/encrypted
    message (detach_sign == False).
    """

    # Accept either an opaque string blob or a Python tuple
    if isinstance(args, StringTypes):
        message = args
    elif isinstance(args, tuple):
        message = canonicalize(args, methodname, methodresponse)

    # Use temporary trustdb
    homedir = mkdtemp()

    cmd = ["gpg", "--batch", "--no-tty",
           "--homedir", homedir,
           "--no-default-keyring",
           "--secret-keyring", secret_keyring,
           "--keyring", keyring,
           "--armor"]

    if detach_sign:
        cmd.append("--detach-sign")
    else:
        cmd.append("--sign")

    p = Popen(cmd, stdin = PIPE, stdout = PIPE, stderr = PIPE)
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

def gpg_verify(args, key, signature = None, methodname = None, methodresponse = False):
    """
    Verifies the signature of the specified method call (methodname !=
    None) or response (methodresponse = True) using the specified
    public key material. If args is not a tuple representing the
    arguments to the method call or the method response value, then it
    should be a string representing a generic message to verify (if
    signature is specified) or verify/decrypt (if signature is not
    specified).
    """

    # Accept either an opaque string blob or a Python tuple
    if isinstance(args, StringTypes):
        message = args
    else:
        message = canonicalize(args, methodname, methodresponse)

    # Write public key to temporary file
    if os.path.exists(key):
        keyfile = None
        keyfilename = key
    else:
        keyfile = NamedTemporaryFile(suffix = '.pub')
        keyfile.write(key)
        keyfile.flush()
        keyfilename = keyfile.name

    # Import public key into temporary keyring
    homedir = mkdtemp()
    call(["gpg", "--batch", "--no-tty", "--homedir", homedir, "--import", keyfilename],
         stdin = PIPE, stdout = PIPE, stderr = PIPE)

    cmd = ["gpg", "--batch", "--no-tty",
           "--homedir", homedir]

    if signature is not None:
        # Write detached signature to temporary file
        sigfile = NamedTemporaryFile()
        sigfile.write(signature)
        sigfile.flush()
        cmd += ["--verify", sigfile.name, "-"]
    else:
        # Implicit signature
        sigfile = None
        cmd.append("--decrypt")

    p = Popen(cmd, stdin = PIPE, stdout = PIPE, stderr = PIPE)
    p.stdin.write(message)
    p.stdin.close()
    if signature is None:
        message = p.stdout.read()
    err = p.stderr.read()
    rc = p.wait()

    # Clean up
    shutil.rmtree(homedir)
    if sigfile:
        sigfile.close()
    if keyfile:
        keyfile.close()

    if rc:
        raise PLCAuthenticationFailure, "GPG verification failed with return code %d: %s" % (rc, err)

    return message
