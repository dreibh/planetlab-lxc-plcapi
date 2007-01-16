import os
import sys
from types import StringTypes
from subprocess import Popen, PIPE

from PLC.Debug import log
from PLC.Faults import *

def sendmail(api, To, Subject, Body, From = None, Cc = "", Bcc = "", DSN = "never"):
    """
    Uses sendmail (must be installed and running locally) to send a
    message to the specified recipients. If the API is running under
    mod_python, the apache user must be listed in e.g.,
    /etc/mail/trusted-users.

    If dsn is not 'never' (e.g., 'failure', 'delay', or 'success'),
    then the current support address (PLC_MAIL_SUPPORT_ADDRESS) will
    receive any delivery status notification messages.
    """

    # Fix up defaults
    if From is None:
        From = "%s Support <%s>" % \
               (api.config.PLC_NAME, api.config.PLC_MAIL_SUPPORT_ADDRESS)

    header = {'From': From,
              'version': sys.version.split(" ")[0],
              'Subject': Subject}

    # Accept either a string or a list of strings for each of To, Cc, and Bcc
    for line in 'To', 'Cc', 'Bcc':
        addresses = locals()[line]
        if isinstance(addresses, StringTypes):
            header[line] = addresses
        else:
            header[line] = ", ".join(addresses)

    if not api.config.PLC_MAIL_ENABLED:
        print >> log, "From: %(From)s, To: %(To)s, Subject: %(Subject)s" % header
        return

    p = Popen(["sendmail", "-N", DSN, "-t", "-f" + api.config.PLC_MAIL_SUPPORT_ADDRESS],
              stdin = PIPE, stdout = PIPE, stderr = PIPE)

    # Write headers
    p.stdin.write("""
Content-type: text/plain
From: %(From)s
Reply-To: %(From)s
To: %(To)s
Cc: %(Cc)s
Bcc: %(Bcc)s
X-Mailer: Python/%(version)s
Subject: %(Subject)s

""".lstrip() % header)

    # Write body
    p.stdin.write(Body)

    p.stdin.close()
    err = p.stderr.read()
    rc = p.wait()

    # Done
    if rc != 0:
        raise PLCAPIError, err
