

from pyaspects.weaver import weave_class_method

from PLC.Method import Method
from aspects.omfaspects import OMFAspect



def apply_omf_aspect():
    # track all PLC methods to add OMF hooks
    weave_class_method(OMFAspect(), Method, "__call__")


def apply_debugger_aspect():
    # just log all method calls w/ their parameters
    from pyaspects.debuggeraspect import DebuggerAspect
    weave_class_method(DebuggerAspect(out=open("/tmp/all_method_calls.log", "a")), Method, "__call__")


