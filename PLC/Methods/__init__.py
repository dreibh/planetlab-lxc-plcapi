#!/usr/bin/python -tt

import os
native_methods = []
toppath = os.path.dirname(__file__)
for path, dirs, methods in os.walk(toppath):
    remove_dirs = []
    for dir in dirs:
        if dir.startswith("."):
            remove_dirs.append(dir)
    for dir in remove_dirs:
        dirs.remove(dir)
    prefix = path + "/"
    prefix = prefix[len(toppath) + 1:].replace("/", ".")
    for method in methods:
        if method == "__init__.py":
            continue
        if not method.endswith(".py"):
            continue
        native_methods.append(prefix + method[:-3])
