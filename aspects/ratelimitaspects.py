#!/usr/bin/python
#-*- coding: utf-8 -*-
#
# S.Çağlar Onur <caglar@cs.princeton.edu>

from PLC.Config import Config
from PLC.Faults import PLCPermissionDenied

from datetime import datetime, timedelta

from pyaspects.meta import MetaAspect

import memcache

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

    def before(self, wobj, data, *args, **kwargs):
        # ratelimit_128.112.139.115_201011091532 = 1
        # ratelimit_128.112.139.115_201011091533 = 14
        # ratelimit_128.112.139.115_201011091534 = 11
        # Now, on every request we work out the keys for the past five minutes and use get_multi to retrieve them. 
        # If the sum of those counters exceeds the maximum allowed for that time period, we block the request.

        api_method_name = wobj.name
        api_method_source = wobj.source

        # FIXME: Support  SessionAuth, GPGAuth, BootAuth and AnonymousAuth
        try:
            api_method_caller = args[0]["Username"]
        except KeyError:
            api_method_caller = "_"

        if api_method_source == None or api_method_source[0] == self.config.PLC_API_IP or api_method_source[0] in self.whitelist:
            return

        if api_method_caller == None:
            self.log("%s called from %s with Username = None" % (api_method_name, api_method_source[0]))
            return

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

        result = mc.get_multi(keys_to_check)
        total_requests = 0
        for i in result:
            total_requests += result[i]

        if total_requests > self.requests:
            self.log("%s - %s" % (api_method_source[0], api_method_caller))
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
