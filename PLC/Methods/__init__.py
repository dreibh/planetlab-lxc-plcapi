#!/usr/bin/python -tt

from __future__ import print_function

import os
import glob

native_methods = []
toppath = os.path.dirname(__file__)

# do not blindly scan this directory, as when using devel tools
# like `make sync` we can easily end up with more files than needed
# which breaks in production

contents = [
    ('.', '[A-Z][a-zA-Z]*.py'),
    ('system', '[a-zA-Z]*.py'),
]

for dir, pattern in contents:
    matches = glob.glob("{}/{}/{}".format(toppath, dir, pattern))
    # count 2 slashes
    prefix = len(toppath) + 1 + len(dir) + 1
    for match in matches:
        filename = match[prefix:][:-3]
        python_name = filename if dir == '.' \
            else "{}.{}".format(dir, filename)
        native_methods.append(python_name)

if __name__ == '__main__':
    native_methods.sort()
    print(native_methods)
