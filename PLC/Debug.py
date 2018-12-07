# log system for PLCAPI
import time
import sys
import syslog

from PLC.Logger import logger

def profile(callable):
    """
    Prints the runtime of the specified callable. Use as a decorator, e.g.,

        @profile
        def foo(...):
            ...

    Or, equivalently,

        def foo(...):
            ...
        foo = profile(foo)

    Or inline:

        result = profile(foo)(...)
    """

    def wrapper(*args, **kwds):
        start = time.time()
        result = callable(*args, **kwds)
        end = time.time()
        args = list(map(str, args))
        args += ["%s = %s" % (name, str(value)) for (name, value) in list(kwds.items())]
        logger.info("%s (%s): %f s" % (callable.__name__, ", ".join(args), end - start))
        return result

    return wrapper

if __name__ == "__main__":
    def sleep(seconds = 1):
        time.sleep(seconds)

    sleep = profile(sleep)

    sleep(1)
