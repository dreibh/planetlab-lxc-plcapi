from pyaspects.weaver import weave_class_method

from PLC.Method import Method
from aspects.ratelimitaspects import RateLimitAspect

def apply_ratelimit_aspect():
    weave_class_method(RateLimitAspect(), Method, "__call__")

def apply_debugger_aspect():
    # just log all method calls w/ their parameters
    from pyaspects.debuggeraspect import DebuggerAspect
    weave_class_method(DebuggerAspect(out=open("/tmp/all_method_calls.log", "a")), Method, "__call__")


