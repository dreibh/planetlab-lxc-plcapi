#!/usr/bin/python
#
# Setup script for PLCAPI
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: setup.py,v 1.7 2007/01/30 11:37:02 thierry Exp $
#

from distutils.core import setup
from glob import glob

setup(py_modules = ['ModPython'],
      packages = ['PLC', 'PLC/Methods', 'PLC/Methods/system'],
      scripts = ['plcsh', 'Server.py', 'Test.py'],
      data_files = [('', ['planetlab4.sql']),
                    ('php', ['php/plc_api.php']),
                    ('migrations', ['migrations/README.txt'] + glob('migrations/[0-9][0-9][0-9]*.sql')),
                    ])
