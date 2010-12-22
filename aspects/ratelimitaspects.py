#!/usr/bin/python
#-*- coding: utf-8 -*-
#
# S.Çağlar Onur <caglar@cs.princeton.edu>

from PLC.Config import Config
from PLC.Faults import PLCPermissionDenied

from PLC.Nodes import Node, Nodes
from PLC.Persons import Person, Persons
from PLC.Sessions import Session, Sessions

from datetime import datetime, timedelta

from pyaspects.meta import MetaAspect

import memcache

import os
import sys
import socket

class BaseRateLimit(object):

    def __init__(self):
        self.config = Config("/etc/planetlab/plc_config")

        # FIXME: change with Config values
        self.prefix = "ratelimit"
        self.minutes = 5 # The time period
        self.requests = 50 # Number of allowed requests in that time period
        self.expire_after = (self.minutes + 1) * 60

        self.whitelist = []

    def log(self, line):
        log = open("/var/log/plc_api_ratelimit.log", "a")
        date = datetime.now().strftime("%d/%m/%y %H:%M")
        log.write("%s - %s\n" % (date, line))
        log.flush()

    def mail(self, to):
        sendmail = os.popen("/usr/sbin/sendmail -N never -t -f%s" % self.config.PLC_MAIL_SUPPORT_ADDRESS, "w")

        subject = "[PLCAPI] Maximum allowed number of API calls exceeded"

        header = {'from': "%s Support <%s>" % (self.config.PLC_NAME, self.config.PLC_MAIL_SUPPORT_ADDRESS),
               'to': "%s, %s" % (to, self.config.PLC_MAIL_SUPPORT_ADDRESS),
               'version': sys.version.split(" ")[0],
               'subject': subject}

        body = "Maximum allowed number of API calls exceeded for the user %s within the last %s minutes." % (to, self.minutes)

        # Write headers
        sendmail.write(
"""
Content-type: text/plain
From: %(from)s
Reply-To: %(from)s
To: %(to)s
X-Mailer: Python/%(version)s
Subject: %(subject)s

""".lstrip() % header)

        # Write body
        sendmail.write(body)
        # Done
        sendmail.close()

    def before(self, wobj, data, *args, **kwargs):
        # ratelimit_128.112.139.115_201011091532 = 1
        # ratelimit_128.112.139.115_201011091533 = 14
        # ratelimit_128.112.139.115_201011091534 = 11
        # Now, on every request we work out the keys for the past five minutes and use get_multi to retrieve them. 
        # If the sum of those counters exceeds the maximum allowed for that time period, we block the request.

        api_method_name = wobj.name
        api_method_source = wobj.source

        try:
            api_method = args[0]["AuthMethod"]
        except:
            return

        # decode api_method_caller
        if api_method == "session":
            api_method_caller = Sessions(wobj.api, {'session_id': args[0]["session"]})
            if api_method_caller == []:
                return
            elif api_method_caller[0]["person_id"] != None:
                api_method_caller = Persons(wobj.api, api_method_caller[0]["person_id"])[0]["email"]
            elif api_method_caller[0]["node_id"] != None:
                api_method_caller = Nodes(wobj.api, api_method_caller[0]["node_id"])[0]["hostname"]
            else:
                api_method_caller = args[0]["session"]
        elif api_method == "password" or api_method == "capability":
            api_method_caller = args[0]["Username"]
        elif api_method == "gpg":
            api_method_caller = args[0]["name"]
        elif api_method == "hmac" or api_method == "hmac_dummybox":
            api_method_caller = args[0]["node_id"]
        elif api_method == "anonymous":
            api_method_caller = "anonymous"
        else:
            api_method_caller = "unknown"

        # excludes
        if api_method_source == None or api_method_source[0] == socket.gethostbyname(self.config.PLC_API_HOST) or api_method_source[0] in self.whitelist:
            return

        # sanity check
        if api_method_caller == None:
            self.log("%s called from %s with Username = None?" % (api_method_name, api_method_source[0]))
            return

        # normalize unicode string otherwise memcache throws an exception
        api_method_caller = str(api_method_caller)

        mc = memcache.Client(["%s:11211" % self.config.PLC_API_HOST])
        now = datetime.now()

        current_key = "%s_%s_%s_%s" % (self.prefix, api_method_caller, api_method_source[0], now.strftime("%Y%m%d%H%M"))
        keys_to_check = ["%s_%s_%s_%s" % (self.prefix, api_method_caller, api_method_source[0], (now - timedelta(minutes = minute)).strftime("%Y%m%d%H%M")) for minute in range(self.minutes + 1)]

        try:
            value = mc.incr(current_key)
        except ValueError:
            value = None

        if value == None:
            mc.set(current_key, 1, time=self.expire_after)

        results = mc.get_multi(keys_to_check)
        total_requests = 0
        for i in results:
            total_requests += results[i]

        if total_requests > self.requests:
            self.log("%s - %s" % (api_method_source[0], api_method_caller))

            caller_key = "%s_%s" % (self.prefix, api_method_caller)
            if mc.get(caller_key) == None:
                mc.set(caller_key, 1, time = self.expire_after)
                if (api_method == "session" and api_method_caller.__contains__("@")) or (api_method == "password" or api_method == "capability"):
                    self.mail(api_method_caller)

            raise PLCPermissionDenied, "Maximum allowed number of API calls exceeded"

    def after(self, wobj, data, *args, **kwargs):
        return

class RateLimitAspect_class(BaseRateLimit):
    __metaclass__ = MetaAspect
    name = "ratelimitaspect_class"

    def __init__(self):
        BaseRateLimit.__init__(self)

    def before(self, wobj, data, *args, **kwargs):
        BaseRateLimit.before(self, wobj, data, *args, **kwargs)

    def after(self, wobj, data, *args, **kwargs):
        BaseRateLimit.after(self, wobj, data, *args, **kwargs)

RateLimitAspect = RateLimitAspect_class
