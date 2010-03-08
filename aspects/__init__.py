

from pyaspects.weaver import weave_class_method

from PLC.Method import Method
from aspects.omfaspects import OMFAspect


def apply_aspects():

    # TEST
    #from pyaspects.debuggeraspect import DebuggerAspect
    #weave_class_method(DebuggerAspect(out=open("/tmp/all_method_calls.log", "a")), Method, "__call__")

    # track all PLC methods to add OMF hooks
    weave_class_method(OMFAspect(), Method, "__call__")
